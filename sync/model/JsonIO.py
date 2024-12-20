import json
import yaml
import os
import re

class JsonIO:
    def write(self, file):
        assert isinstance(self, dict)

        _, ext = os.path.splitext(file)

        file.parent.mkdir(parents=True, exist_ok=True)


        if ext.lower() == '.yaml':
            with open(file, "w") as f:
                yaml.dump(self, f, indent=2)

        else:
            with open(file, "w") as f:
                json.dump(self, f, indent=2)

    @classmethod
    def filter(cls, text):
        return re.sub(r",(?=\s*?[}\]])", "", text)

    @classmethod
    def filterArray(cls, filter, toFilter):
        return [i for i in filter if i in toFilter]
 
    @classmethod
    def load(cls, file):
        
        _, ext = os.path.splitext(file)
        
        if ext.lower() == '.yaml':
            with open(file, encoding="utf-8", mode="r") as f:
                text = cls.filter(f.read())
                obj = yaml.load(text, Loader=yaml.FullLoader)

                assert isinstance(obj, dict)
        else: 
            with open(file, encoding="utf-8", mode="r") as f:
                text = cls.filter(f.read())
                obj = json.loads(text)

                assert isinstance(obj, dict)

        return obj
