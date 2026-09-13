def test_pin_as_user(driver):
    n1=driver.click_new_note(); driver.type_in_editor("first")
    n2=driver.click_new_note(); driver.type_in_editor("second")
    # pin first (oldest) -> should bubble to top despite updated_at
    rows=driver.get_notes()
    oldest=min(rows, key=lambda r: r["created_at"])
    driver.app.db.toggle_pin(oldest["id"]); driver.app._on_saved()
    top=driver.get_notes()[0]
    assert top["pinned"]==1
    assert top["id"]==oldest["id"]
    # pinned_only filter
    driver.app.set_search("", pinned_only=True)
    assert driver.notes_count(pinned_only=True)==1
    driver.app.set_search("", pinned_only=False)

def test_lock_as_user(driver):
    nid=driver.click_new_note(); driver.type_in_editor("secret #private")
    assert driver.app.db.get_note(nid)["locked"]==0
    driver.app.db.toggle_lock(nid)
    assert driver.app.db.get_note(nid)["locked"]==1
    driver.app.db.toggle_lock(nid)
    assert driver.app.db.get_note(nid)["locked"]==0
