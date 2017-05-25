# -*- coding: utf8 -*-

from peewee import CharField, TextField, ForeignKeyField, FloatField, IntegerField, BooleanField, DateTimeField

from os.path import basename

import settings
import utils
from db import db


class Place(db.Model):

    name = CharField()
    tz = CharField(default='Europe/Paris')
    modified = CharField()

    @classmethod
    def update_or_create(cls, place):
        try:
            p = cls.get(id=place['id'])
            p.name = place.get('name')
            p.tz = place.get('tz')
            p.modified = place.get('modified')
            p.save()
        except cls.DoesNotExist:
            p = cls.create(id=place['id'], name=place.get('name'), tz=place.get('tz'), modified=place.get('modified'))
        return p


class Event(db.Model):

    name = CharField()
    modified = CharField()

    @classmethod
    def update_or_create(cls, event):
        try:
            e = cls.get(id=event['id'])
            e.name = event.get('name')
            e.modified = event.get('modified')
            e.save()
        except cls.DoesNotExist:
            e = cls.create(id=event['id'], name=event.get('name'), modified=event.get('modified'))
        return e


class TicketTemplate(db.Model):

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

    @classmethod
    def update_or_create(cls, ticket_template):

        try:
            tt = cls.get(TicketTemplate.id == ticket_template['id'])
            tt.html = ticket_template['html']
            tt.title = ticket_template['title']
            tt.description = ticket_template['description']
            tt.modified = ticket_template['modified']
            tt.save()
        except cls.DoesNotExist:
            tt = cls.create(**ticket_template)

        for text_variable in ticket_template['text_variables']:
            TextVariable.update_or_create(text_variable, ticket_template=tt)

        for image_variable in ticket_template['image_variables']:
            ImageVariable.update_or_create(image_variable, ticket_template=tt)

        for image in ticket_template['images']:
            Image.update_or_create(image, ticket_template=tt)

        return tt


class TextVariable(db.Model):

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

    @classmethod
    def update_or_create(cls, text_variable, ticket_template=None):
        try:
            tv = cls.get(TextVariable.id == text_variable['id'])
            if tv.name != text_variable.get('name') or tv.mode != text_variable.get('mode'):
                tv.name = text_variable.get('name')
                tv.mode = text_variable.get('mode')
                tv.save()
            text_ids = [item['id'] for item in text_variable['items']]
            query = Text.select().where(~(Text.id << text_ids)).join(TextVariable).where(TextVariable.id == text_variable['id'])
            for text in query:
                text.delete_instance()
        except cls.DoesNotExist:
            tv = cls.create(ticket_template=ticket_template, **text_variable)
        for text in text_variable['items']:
            Text.update_or_create(text, tv)
        return tv


class Text(db.Model):

    value = TextField()
    variable = ForeignKeyField(TextVariable, related_name='items', null=True)

    def serialize(self):
        return {'id': self.id, 'text': self.value}

    @classmethod
    def update_or_create(cls, text, variable=None):
        try:
            txt = Text.get(cls.id == text['id'])
            if txt.value != text['text']:
                txt.value = text['text']
                txt.save()
            return txt
        except cls.DoesNotExist:
            return Text.create(id=text['id'], value=text['text'], variable=variable)


class ImageVariable(db.Model):

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

    @classmethod
    def update_or_create(cls, image_variable, ticket_template=None):
        try:
            iv = cls.get(ImageVariable.id == image_variable['id'])
            if iv.name != image_variable.get('name') or iv.mode != image_variable.get('mode'):
                iv.name = image_variable.get('name')
                iv.mode = image_variable.get('mode')
                iv.save()
            image_ids = [item['id'] for item in image_variable['items']]
            query = Image.select().where(~(Image.id << image_ids)).join(ImageVariable).where(ImageVariable.id == image_variable['id'])
            for image in query:
                image.delete_instance()
        except cls.DoesNotExist:
            iv = cls.create(ticket_template=ticket_template, **image_variable)
        for image in image_variable['items']:
            Image.update_or_create(image, variable=iv)
        return iv


class Image(db.Model):

    path = TextField()
    variable = ForeignKeyField(ImageVariable, related_name='items', null=True)
    ticket_template = ForeignKeyField(TicketTemplate, related_name='images', null=True)

    def serialize(self):
        return {'id': self.id, 'name': basename(self.path)}

    @classmethod
    def update_or_create(cls, image, variable=None, ticket_template=None):
        try:
            img = cls.get(Image.id == image['id'])
            if basename(img.path) != image['name']:
                path = utils.download(image['image'], settings.IMAGE_ROOT)
                img.path = path
                img.save()
            return img
        except cls.DoesNotExist:
            path = utils.download(image['image'], settings.IMAGE_ROOT)
            return cls.create(id=image['id'], path=path, variable=variable, ticket_template=ticket_template)


class Photobooth(db.Model):

    uuid = CharField(unique=True)
    serial_number = CharField(null=True)
    place = ForeignKeyField(Place, null=True)
    event = ForeignKeyField(Event, null=True)
    ticket_template = ForeignKeyField(TicketTemplate, null=True)
    paper_level = FloatField(default=100.0)
    counter = IntegerField(default=0)

    def update_from_api_data(self, photobooth):

        update_dict = {}

        if self.id != photobooth['id']:
            update_dict['id'] = photobooth['id']

        serial_number = photobooth.get('serial_number')
        if self.serial_number != serial_number:
            update_dict['serial_number'] = serial_number

        # check if we need to update the place
        place = photobooth.get('place')

        if place and not self.place:
            p = Place.update_or_create(place)
            update_dict['place'] = p

        elif not place and self.place:
            self.place.delete_instance()
            update_dict['place'] = None

        elif place and self.place and place.get('id') != self.place.id:
            self.place.delete_instance()
            p = Place.update_or_create(place)
            update_dict['place'] = p

        elif place and self.place and place.get('modified') > self.place.modified:
            self.place.name = place.get('name')
            self.place.tz = place.get('tz')
            self.place.modified = place.get('modified')
            self.place.save()

        # check if we need to update the event
        event = photobooth.get('event')
        if event and not self.event:
            e = Event.update_or_create(event)
            update_dict['event'] = e

        elif not event and self.event:
            self.event.delete_instance()
            update_dict['event'] = None

        elif event and self.event and event.get('id') != self.event.id:
            self.event.delete_instance()
            e = Event.update_or_create(event)
            update_dict['event'] = e

        elif event and self.event and event.get('modified') > self.event.modified:
            self.event.name = event.get('name')
            self.event.modified = event.get('modified')
            self.event.save()

        # check if we need to update the ticket template
        ticket_template = photobooth.get('ticket_template')

        if ticket_template and not self.ticket_template:
            t = TicketTemplate.update_or_create(ticket_template)
            update_dict['ticket_template'] = t

        elif not ticket_template and self.ticket_template:
            self.ticket_template.delete_instance()
            update_dict['ticket_template'] = None

        elif ticket_template and self.ticket_template and ticket_template.get('id') != self.ticket_template.id:
            self.ticket_template.delete_instance()
            t = TicketTemplate.update_or_create(ticket_template)
            update_dict['ticket_template'] = t

        elif ticket_template and self.ticket_template and ticket_template.get('modified') > self.ticket_template.modified:
            TicketTemplate.update_or_create(ticket_template)

        if update_dict:
            q = Photobooth.update(**update_dict).where(Photobooth.uuid == settings.RESIN_UUID)
            return q.execute()
        
        return 0


class Code(db.Model):

    value = CharField()

    @staticmethod
    def pop():
        code = Code.select().limit(1)[0]
        value = code.value
        code.delete_instance()
        return value

    @staticmethod
    def less_than_1000_left():
        return Code.select().count() < 1000

    @staticmethod
    def bulk_insert(codes):
        with db.database.atomic():
            for code in codes:
                Code.create(value=code)


class Portrait(db.Model):

    code = CharField()
    taken = DateTimeField()
    place_id = CharField(null=True)
    event_id = CharField(null=True)
    photobooth_id = CharField()
    ticket = CharField()
    picture = CharField()
    uploaded = BooleanField(default=False)

    @staticmethod
    def not_uploaded():
        return Portrait.select().where(~ Portrait.uploaded)

    @staticmethod
    def first_not_uploaded():
        """ return first portrait to be uploaded """
        try:
            return Portrait.not_uploaded().get()
        except Portrait.DoesNotExist:
            return None

    @staticmethod
    def not_uploaded_count():
        """ Retrieves the number of portraits to be uploaded """
        return Portrait.not_uploaded().count()


def get_all_models():
    return [
        Place,
        Event,
        Text,
        Image,
        TextVariable,
        ImageVariable,
        TicketTemplate,
        Portrait,
        Photobooth,
        Code
    ]
