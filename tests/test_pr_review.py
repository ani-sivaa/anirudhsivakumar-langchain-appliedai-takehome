import pytest
from agent.nodes.git import get_git_diff
from agent.nodes.review import review_file
from agent.nodes.summarize import summarize_review


def test_review_file():
    state = {
        "file": "test.py",
        "diff": """--- a/test.py
+++ b/test.py
@@ -1,3 +1,5 @@
 def hello():
-    print("hello")
+    name = input()
+    print("hello " + name)
"""
    }
    
    result = review_file(state)
    
    assert "review_comments" in result
    assert len(result["review_comments"]) > 0
    assert "test.py" in result["review_comments"][0]


def test_review_file_missing_data():
    state = {}
    result = review_file(state)
    
    assert "review_comments" in result
    assert "Error" in result["review_comments"][0]


def test_summarize_single_review():
    state = {"review_comments": ["**test.py**\nLooks good"]}
    result = summarize_review(state)
    
    assert "review_summary" in result
    assert "test.py" in result["review_summary"]


def test_summarize_no_comments():
    state = {"review_comments": []}
    result = summarize_review(state)
    
    assert result["review_summary"] == "No review comments available."


def test_summarize_multiple_reviews():
    state = {
        "review_comments": [
            "**file1.py**\nGood changes",
            "**file2.py**\nNeeds improvement"
        ]
    }
    
    result = summarize_review(state)
    
    assert "review_summary" in result
    assert "file1.py" in result["review_summary"]
    assert "file2.py" in result["review_summary"]

