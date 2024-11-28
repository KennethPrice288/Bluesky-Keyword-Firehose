import re

class Matcher:
    @staticmethod
    def matches_keywords(text, keywords, mode='OR'):
        if mode == 'OR':
            return any(re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE) 
                      for keyword in keywords)
        if mode == 'AND':
            return all(re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE) 
                  for keyword in keywords)
        return False
