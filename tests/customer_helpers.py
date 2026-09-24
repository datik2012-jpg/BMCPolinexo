def fill_customer(card, identity='999999999'):
    card.get_by_label('קרבה משפחתית', exact=True).select_option(label='לקוח ראשי')
    card.get_by_label('שם פרטי', exact=True).fill('לקוח')
    card.get_by_label('שם משפחה', exact=True).fill('סינתטי')
    card.get_by_label('תעודת זהות', exact=True).fill(identity)
    card.get_by_label('תאריך לידה', exact=True).fill('1990-01-01')
    card.get_by_label('מין', exact=True).select_option(label='זכר')
    card.get_by_label('עישון', exact=True).select_option(label='לא מעשן/ת')
