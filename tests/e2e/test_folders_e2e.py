def test_folders_flow_as_user(driver):
    fid=driver.create_folder("Work")
    assert any(r["name"]=="Work" for r in driver.app.db.list_folders())
    # create note in Work
    driver.app.select_folder(fid)
    nid=driver.click_new_note()
    driver.type_in_editor("Work note")
    # All Notes sees it, Work sees it, Ideas (empty) doesn't
    assert driver.notes_count(folder_id="__all__")==1
    assert driver.notes_count(folder_id=fid)==1
    fid2=driver.create_folder("Ideas")
    driver.app.select_folder(fid2)
    assert driver.notes_count(folder_id=fid2)==0
    # rename
    driver.rename_folder(fid, "Work-Renamed")
    assert any(r["name"]=="Work-Renamed" for r in driver.app.db.list_folders())
    # delete folder -> note moves to All (folder_id NULL)
    driver.delete_folder(fid)
    assert driver.notes_count(folder_id="__all__")==1

def test_drag_note_between_folders_logic(driver):
    a=driver.create_folder("A"); b=driver.create_folder("B")
    driver.app.select_folder(a); nid=driver.click_new_note(); driver.type_in_editor("in A")
    assert driver.notes_count(folder_id=a)==1
    # simulate drag by updating folder_id
    import time
    driver.app.db.update_note(nid, "in A", "in A", int(time.time()), folder_id=b)
    assert driver.notes_count(folder_id=a)==0
    assert driver.notes_count(folder_id=b)==1
