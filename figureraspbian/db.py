from peewee import *
from os.path import join, basename

from figureraspbian import settings
from figureraspbian.utils import pixels2cm, download


database = SqliteDatabase(join(settings.DATA_ROOT, 'local.db'))


def get_tables():
    return [
        Place,
        Event,
        TicketTemplate,
        TextVariable,
        Text,
        ImageVariable,
        Image,
        Photobooth,
        Code,
        Portrait]


def init():
    database.connect()
    # creates tables if not exist
    database.create_tables(get_tables(), True)
    # always create a record for photobooth
    Photobooth.get_or_create(uuid=settings.RESIN_UUID)
    database.close()


def erase():
    database.drop_tables(get_tables(), True)


def close():
    database.close()


class BaseModel(Model):

    class Meta:
        database = database


class Place(BaseModel):

    name = CharField()
    tz = CharField(default='Europe/Paris')
    modified = CharField()


class Event(BaseModel):

    name = CharField()
    modified = CharField()


class TicketTemplate(BaseModel):

    html = TextField()
    title = TextField(null=True)
    description = TextField(null=True)
    modified = CharField()

    def serialize(self):
        data = self.__dict__['_data']
        data['images'] = [image.serialize() for image in self.images]
        data['text_variables'] = [text_variable.serialize() for text_variable in self.text_variables]
        data['image_variables'] = [image_variable.serialize() for image_variable in self.image_variables]
        return data


class TextVariable(BaseModel):

    name = CharField()
    ticket_template = ForeignKeyField(TicketTemplate, null=True, related_name='text_variables')
    mode = CharField()

    def serialize(self):
        data = {
            'id': self.id,
            'name': self.name,
            'mode': self.mode,
            'items': [text.serialize() for text in self.items]
        }
        return data


class Text(BaseModel):

    value = TextField()
    variable = ForeignKeyField(TextVariable, related_name='items', null=True)

    def serialize(self):
        return {'id': self.id, 'text': self.value}


class ImageVariable(BaseModel):

    name = CharField()
    ticket_template = ForeignKeyField(TicketTemplate, null=True, related_name='image_variables')
    mode = CharField()

    def serialize(self):
        data = {
            'id': self.id,
            'name': self.name,
            'mode': self.mode,
            'items': [image.serialize() for image in self.items]
        }
        return data


class Image(BaseModel):

    path = TextField()
    variable = ForeignKeyField(ImageVariable, related_name='items', null=True)
    ticket_template = ForeignKeyField(TicketTemplate, related_name='images', null=True)

    def serialize(self):
        return {'id': self.id, 'name': basename(self.path)}


class Photobooth(BaseModel):

    uuid = CharField(unique=True)
    serial_number = CharField(null=True)
    place = ForeignKeyField(Place, null=True)
    event = ForeignKeyField(Event, null=True)
    ticket_template = ForeignKeyField(TicketTemplate, null=True)
    paper_level = FloatField(default=100.0)
    counter = IntegerField(default=0)


class Code(BaseModel):

    value = CharField()


class Portrait(BaseModel):

    code = CharField()
    taken = DateTimeField()
    place_id = CharField(null=True)
    event_id = CharField(null=True)
    photobooth_id = CharField()
    ticket = CharField()
    picture = CharField()
    uploaded = BooleanField(default=False)


def get_photobooth():
    return Photobooth.get(Photobooth.uuid == settings.RESIN_UUID)


def get_code():
    code = Code.select().limit(1)[0]
    value = code.value
    code.delete_instance()
    return value


def get_number_of_portraits_to_be_uploaded():
    """ Retrieves the number of portraits to be uploaded """
    return Portrait.select().where(~ Portrait.uploaded).count()


def get_portrait_to_be_uploaded():
    """ return first portrait to be uploaded """
    try:
        return Portrait.select().where(~ Portrait.uploaded).get()
    except Portrait.DoesNotExist:
        return None


def get_portraits_to_be_uploaded():
    return Portrait.select().filter(uploaded=False)


def create_portrait(portrait):
    return Portrait.create(
        code=portrait['code'],
        taken=portrait['taken'],
        place_id=portrait['place'],
        event_id=portrait['event'],
        photobooth_id=portrait['photobooth'],
        ticket=portrait['ticket'],
        picture=portrait['picture']
    )


def create_place(place):
    return Place.create(
        id=place['id'],
        name=place.get('name'),
        tz=place.get('tz'),
        modified=place.get('modified')
    )


def create_event(event):
    return Event.create(
        id=event['id'],
        name=event.get('name'),
        modified=event.get('modified')
    )


def update_or_create_text(text, variable=None):
    try:
        txt = Text.get(Text.id == text['id'])
        if txt.value != text['text']:
            txt.value = text['text']
            txt.save()
        return txt
    except Text.DoesNotExist:
        return Text.create(id=text['id'], value=text['text'], variable=variable)


def update_or_create_text_variable(text_variable, ticket_template=None):
    try:
        tv = TextVariable.get(TextVariable.id == text_variable['id'])
        if tv.name != text_variable.get('name') or tv.mode != text_variable.get('mode'):
            tv.name = text_variable.get('name')
            tv.mode = text_variable.get('mode')
            tv.save()
        text_ids = [item['id'] for item in text_variable['items']]
        query = Text.select().where(~(Text.id << text_ids)).join(TextVariable).where(TextVariable.id == text_variable['id'])
        for text in query:
            text.delete_instance()
    except TextVariable.DoesNotExist:
        tv = TextVariable.create(
            id=text_variable['id'],
            name=text_variable.get('name'),
            mode=text_variable.get('mode'),
            ticket_template=ticket_template)
    for text in text_variable['items']:
        update_or_create_text(text, tv)
    return tv


def update_or_create_image(image, variable=None, ticket_template=None):
    try:
        img = Image.get(Image.id == image['id'])
        if basename(img.path) != image['name']:
            path = download(image['image'], settings.IMAGE_ROOT)
            img.path = path
            img.save()
        return img
    except Image.DoesNotExist:
        path = download(image['image'], settings.IMAGE_ROOT)
        return Image.create(id=image['id'], path=path, variable=variable, ticket_template=ticket_template)


def update_or_create_image_variable(image_variable, ticket_template=None):
    try:
        iv = ImageVariable.get(ImageVariable.id == image_variable['id'])
        if iv.name != image_variable.get('name') or iv.mode != image_variable.get('mode'):
            iv.name = image_variable.get('name')
            iv.mode = image_variable.get('mode')
            iv.save()
        image_ids = [item['id'] for item in image_variable['items']]
        query = Image.select().where(~(Image.id << image_ids)).join(ImageVariable).where(ImageVariable.id == image_variable['id'])
        for image in query:
            image.delete_instance()
    except ImageVariable.DoesNotExist:
        iv = ImageVariable.create(
            id=image_variable['id'],
            name=image_variable.get('name'),
            mode=image_variable.get('mode'),
            ticket_template=ticket_template)
    for image in image_variable['items']:
        update_or_create_image(image, variable=iv)
    return iv


def update_or_create_ticket_template(ticket_template):

    try:
        tt = TicketTemplate.get(TicketTemplate.id == ticket_template['id'])
        tt.html = ticket_template['html']
        tt.title = ticket_template['title']
        tt.description = ticket_template['description']
        tt.modified = ticket_template['modified']
        tt.save()
    except TicketTemplate.DoesNotExist:
        tt = TicketTemplate.create(
            id=ticket_template['id'],
            html=ticket_template['html'],
            title=ticket_template['title'],
            description=ticket_template['description'],
            modified=ticket_template['modified']
        )

    for text_variable in ticket_template['text_variables']:
        update_or_create_text_variable(text_variable, tt)

    for image_variable in ticket_template['image_variables']:
        update_or_create_image_variable(image_variable, tt)

    for image in ticket_template['images']:
        update_or_create_image(image, ticket_template=tt)
        
    return tt


def update_photobooth(**kwargs):
    query = Photobooth.update(**kwargs).where(Photobooth.uuid == settings.RESIN_UUID)
    query.execute()


def update_place(id, **kwargs):
    query = Place.update(**kwargs).where(Place.id == id)
    query.execute()


def update_event(id, **kwargs):
    query = Event.update(**kwargs).where(Event.id == id)
    query.execute()


def update_portrait(id, **kwargs):
    query = Portrait.update(**kwargs).where(Portrait.id == id)
    query.execute()


def increment_counter():
    photobooth = get_photobooth()
    photobooth.counter += 1
    photobooth.save()


def update_paper_level(pixels):

    photobooth = Photobooth.get(Photobooth.uuid == settings.RESIN_UUID)
    if pixels == 0:
        # we are out of paper
        new_paper_level = 0
    else:
        old_paper_level = photobooth.paper_level
        if old_paper_level == 0:
            # Someone just refill the paper
            new_paper_level = 100
        else:
            cm = pixels2cm(pixels)
            new_paper_level = old_paper_level - (cm / float(settings.PAPER_ROLL_LENGTH)) * 100
            if new_paper_level <= 1:
                # estimate is wrong, guess it's 10%
                new_paper_level = 10
    photobooth.paper_level = new_paper_level
    photobooth.save()
    return new_paper_level


def delete(instance):
    return instance.delete_instance()


def should_claim_code():
    return Code.select().count() < 1000


def bulk_insert_codes(codes):
    with database.atomic():
        for code in codes:
            Code.create(value=code)
