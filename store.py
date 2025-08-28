
from typing import Dict, Any
import time, random

class MemoryStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get(self, sid: str) -> Dict[str, Any]:
        if sid not in self.sessions:
            self.sessions[sid] = {
                "started_at": time.time(),
                "answers": [],  # list of dicts: {qid, correct: bool, difficulty, topic}
                "streak": 0,
                "level": 1
            }
        return self.sessions[sid]

    def record_answer(self, sid: str, qid: str, correct: bool, difficulty: str, topic: str):
        s = self.get(sid)
        s["answers"].append({"qid": qid, "correct": correct, "difficulty": difficulty, "topic": topic, "t": time.time()})
        if correct:
            s["streak"] += 1
            if s["streak"] % 3 == 0:
                s["level"] = min(10, s["level"] + 1)
        else:
            s["streak"] = 0
            s["level"] = max(1, s["level"] - 1)

    def summary(self, sid: str):
        s = self.get(sid)
        total = len(s["answers"])
        correct = sum(1 for a in s["answers"] if a["correct"])
        accuracy = (correct / total * 100) if total else 0.0
        by_topic = {}
        for a in s["answers"]:
            by_topic.setdefault(a["topic"], {"total":0,"correct":0})
            by_topic[a["topic"]]["total"] += 1
            by_topic[a["topic"]]["correct"] += 1 if a["correct"] else 0
        weak = []
        for t, v in by_topic.items():
            acc = (v["correct"]/v["total"]*100) if v["total"] else 0.0
            weak.append((t, acc))
        weak.sort(key=lambda x: x[1])
        return {
            "level": s["level"],
            "streak": s["streak"],
            "total": total,
            "correct": correct,
            "accuracy": round(accuracy, 1),
            "weak_topics": weak[:3]
        }

STORE = MemoryStore()
