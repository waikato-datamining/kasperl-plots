from typing import List, Dict


def list_classes() -> Dict[str, List[str]]:
    return {
        "seppl.io.Reader": [
            "kasperl.plots.reader",
        ],
        "seppl.io.Writer": [
            "kasperl.plots.writer",
        ],
    }
