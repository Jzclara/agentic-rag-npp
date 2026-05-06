from llama_index.core.node_parser import SentenceSplitter

def get_text_splitter(chunk_size: int = 512, chunk_overlap: int =50) -> SentenceSplitter:
    # SentenceSplitter 按句子边界切分文本，避免从句子中间截断
    # chunk_size: 每个 chunk 最多包含多少个 token
    # chunk_overlap: 相邻 chunk 之间重叠多少 token，防止关键信息被切断
    return SentenceSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap,
    )

# chunk_size=512 和 chunk_overlap=50 的选择

# 说实话，这是经验值，不是测试得出来的。行业里常见的起点是：

# chunk_size 在 256 到 1024 之间
# chunk_overlap 是 chunk_size 的 10%-20%

# 选 512 的考虑是：

# 太小（如 128）——一个 chunk 可能只有半句话，语义不完整
# 太大（如 1024）——检索时召回的内容太宽泛，答案生成容易被无关内容干扰
# 512 对学术论文段落来说大小比较合适，一般能包含一个完整的论点或实验描述
# 我没有在你的语料上测试过，这只是合理的起点。
# 这也是为什么第二阶段要接入 Ragas——到时候你可以把 chunk_size 改成 256 或 1024，重新跑评估，
# 用 faithfulness 和 answer relevancy 的数据来判断哪个更好，而不是靠感觉。