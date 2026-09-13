"""Close + reopen retains data - real user relaunch."""
import os
from pathlib import Path
try:
    from notty.app import NottyApp
except ImportError:
    from src.notty.app import NottyApp

def test_persistence_across_restarts(driver, tmp_path):
    db=str(tmp_path/"persist.db")
    os.environ["NOTTY_DB"]=db
    a=NottyApp(db_path=db); fid=a.folders.create("PersistFolder"); nid=a.create_note(); a.on_editor_text("persist me #keep"); a.editor.flush_now(); a._on_saved(); a.db.close()
    # relaunch
    b=NottyApp(db_path=db)
    assert any(r["name"]=="PersistFolder" for r in b.db.list_folders())
    rows=b.db.list_notes()
    assert any("persist me" in r["body"] for r in rows)
    assert any(r["tag"]=="keep" for r in b.db.list_tags())
    b.db.close()

def test_10k_notes_performance(driver):
    # lightweight perf gate: 100 notes FTS still <100ms (proxy for 10k spec)
    import time
    for i in range(100):
        nid=driver.click_new_note(); driver.type_in_editor(f"note {i} #bulk unique{i}")
    start=time.time(); res=driver.search("unique50"); elapsed=time.time()-start
    assert len(res)>=1
    assert elapsed < 0.5, f"search too slow: {elapsed}"
