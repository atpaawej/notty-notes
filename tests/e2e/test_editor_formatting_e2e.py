from src.notty.features.editor.controller import extract_title_body

def test_editor_title_extraction_and_checklist(driver):
    nid=driver.click_new_note()
    txt="# Title\n- [ ] task one\n- [x] done\nSome **bold** and *italic*"
    driver.type_in_editor(txt)
    row=driver.app.db.get_note(nid)
    assert row["title"].startswith("# Title") or "Title" in row["title"]
    assert "task one" in row["body"]
    # controller helper
    title, body=extract_title_body(txt)
    assert title=="# Title"
    assert body==txt

def test_editor_debounced_save_persistence(driver, tmp_path):
    # type then immediately simulate crash -> flush_now must have saved
    nid=driver.click_new_note()
    driver.app.on_editor_text("unsaved draft #draft")
    # before flush, db still old - after flush, saved
    driver.app.editor.flush_now(); driver.app._on_saved()
    assert "unsaved" in driver.app.db.get_note(nid)["body"]
