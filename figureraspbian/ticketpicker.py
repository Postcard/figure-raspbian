# -*- coding: utf8 -*-

import utils


def weighted_choice(ticket_templates):
    """
    Pick a ticket_template based on probability
    """
    sum_probabilities = sum(ticket_template['probability'] for
                            ticket_template in ticket_templates if
                            ticket_template['probability'])
    assert 0 <= sum_probabilities <= 1
    equiprobable_choices = [ticket_template for
                            ticket_template in ticket_templates if
                            not ticket_template['probability']]
    p = (1.0 - sum_probabilities) / len(equiprobable_choices)
    choices = []
    for ticket_template in ticket_templates:
        choices.append((ticket_template, ticket_template.get('probability') or p))
    return utils.weighted_choice(choices)
