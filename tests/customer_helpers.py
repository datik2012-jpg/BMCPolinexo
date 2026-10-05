def fill_customer(card, identity='999999999'):
    card.get_by_label('קרבה משפחתית', exact=True).select_option(label='לקוח ראשי')
    card.get_by_label('שם פרטי', exact=True).fill('לקוח')
    card.get_by_label('שם משפחה', exact=True).fill('סינתטי')
    card.get_by_label('תעודת זהות', exact=True).fill(identity)
    card.get_by_label('תאריך לידה', exact=True).fill('01/01/1990')
    card.get_by_label('מין', exact=True).select_option(label='זכר')
    card.get_by_label('מצב משפחתי', exact=True).select_option(label='נשוי/אה')
    card.get_by_label('עישון', exact=True).select_option(label='לא מעשן/ת')


def copy_all_to_proposal(scope):
    """Exercise explicit copying before editing any imported coverage."""
    scope.get_by_role('tab', name='מצב קיים').click()
    existing = scope.locator('.existing-section')
    existing.get_by_role('button', name='ניקוי סינון', exact=True).click()
    for policy in existing.locator('.policy').all():
        if policy.get_attribute('open') is None:
            policy.locator(':scope > summary').click()
    copies = existing.get_by_role('button', name='העתקה למצב החדש', exact=True)
    while copies.count():
        copies.first.click()
    scope.get_by_role('tab', name='מצב חדש').click()
    scope.locator('.proposed-section').get_by_role('button', name='ניקוי סינון', exact=True).click()
