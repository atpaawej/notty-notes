def test_search_and_tags_as_user(driver):
    n1=driver.click_new_note(); driver.type_in_editor("alpha meeting #work with attachment idea")
    n2=driver.click_new_note(); driver.type_in_editor("beta personal #personal todo - [ ] buy milk")
    n3=driver.click_new_note(); driver.type_in_editor("gamma #work #personal overlap")
    # tag browser lists both
    tags=dict((r["tag"], r["c"]) for r in driver.list_tags())
    assert tags["work"]==2
    assert tags["personal"]==2
    # filter by tag via AppState path (real user clicks tag)
    driver.app.select_tag("work")
    assert driver.notes_count(tag="work")==2
    driver.app.select_tag("personal")
    assert driver.notes_count(tag="personal")==2
    driver.app.select_tag(None)
    # FTS prefix search instant
    assert len(driver.search("alp"))==1
    assert len(driver.search("meet"))==1
    # combined folder + tag + query
    fid=driver.create_folder("Filtered")
    driver.app.select_folder(fid); nid=driver.click_new_note(); driver.type_in_editor("inside filtered #work unique999")
    # search within folder
    driver.app.select_folder(fid)
    assert len(driver.search("unique999"))==1
    driver.app.select_folder("__all__")
    assert len(driver.search("unique999"))==1
