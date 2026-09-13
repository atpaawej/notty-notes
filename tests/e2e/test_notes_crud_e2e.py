"""E2E: real user CRUD flow."""
def test_create_edit_persist_as_user(driver):
    nid=driver.click_new_note()
    assert driver.notes_count()==1
    driver.type_in_editor("Meeting Notes #work\n- [ ] scaffold project\n- [x] done")
    # verify preview + FTS
    notes=driver.get_notes()
    assert any("Meeting Notes" in n["title"] for n in notes)
    # search as user
    assert len(driver.search("Meeting"))==1
    assert len(driver.search("nonexistent-xyz"))==0
    # tag indexed
    tags=[r["tag"] for r in driver.list_tags()]
    assert "work" in tags
    # reopen note
    txt=driver.open_note(nid)
    assert "scaffold" in txt
    # second note
    nid2=driver.click_new_note()
    driver.type_in_editor("Second note")
    assert driver.notes_count()==2

def test_delete_note(driver):
    nid=driver.click_new_note()
    driver.type_in_editor("to delete")
    assert driver.notes_count()==1
    driver.app.delete_selected()
    assert driver.notes_count()==0
