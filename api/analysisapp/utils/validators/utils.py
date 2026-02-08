from typing import List


def remove_one_string_copy(original_list: List[str],
                           target_string: str) -> List[str]:
    if target_string not in original_list:
        # 対象の文字列がない場合は、元のリストのコピーを返す
        return original_list[:]

    # target_string の最初のインデックスを見つける
    index_to_remove = original_list.index(target_string)

    # スライスを使って、その要素を除いた新しいリストを作成
    return original_list[:index_to_remove] + original_list[index_to_remove+1:]
