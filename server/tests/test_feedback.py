"""用户反馈：可匿名写入并按时间倒序读取"""

from db import create_feedback, delete_feedback, init_db, list_feedback


def test_create_feedback_with_and_without_name():
    init_db()
    named = create_feedback(content="音效太吵了", author_name="测试队长")
    anon = create_feedback(content="希望增加慢放功能", author_name=None)

    assert named["authorName"] == "测试队长"
    assert named["content"] == "音效太吵了"
    assert anon["authorName"] is None
    assert anon["content"] == "希望增加慢放功能"

    items = list_feedback()
    ids = {item["id"] for item in items}
    assert named["id"] in ids
    assert anon["id"] in ids

    assert delete_feedback(named["id"]) is True
    assert delete_feedback(named["id"]) is False
