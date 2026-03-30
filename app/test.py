def longest_common_prefix(text):
    if not text:
        return  ""
    prefix = text[0]

    for t in text[1:]:
        while not t.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    print(prefix)
    return prefix


words = [
    "Go_to_be",
    "Go_to_be_rag",
    "Go_to_be_rag_game",
    "Go_to_be_rag_game_tame"
]

user_input = "Go_to_b"

matches = [w for w in words if w.startswith(user_input)]

if matches:
    completion = longest_common_prefix(matches)
    print(completion)