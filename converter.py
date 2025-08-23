import os
import sys

def convert_sjis_to_utf8(folder_path):
    """
    将指定文件夹下所有.txt文件的编码从Shift JIS转换为UTF-8。

    :param folder_path: 目标文件夹的路径。
    """
    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在。")
        return

    print(f"开始转换文件夹 '{folder_path}' 中的.txt文件...")

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            try:
                # 以Shift JIS编码读取文件内容
                with open(file_path, 'r', encoding='shift_jis', errors='ignore') as f:
                    content = f.read()

                # 以UTF-8编码写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"成功转换文件: {filename}")

            except FileNotFoundError:
                print(f"错误: 文件未找到 - {filename}")
            except UnicodeDecodeError:
                print(f"解码错误: {filename} 可能不是Shift JIS编码，或者文件已损坏。")
            except Exception as e:
                print(f"转换失败: {filename} - {e}")

    print("所有.txt文件转换完成。")

if __name__ == "__main__":
    # ##################################################
    # 请在这里修改为您要转换的文件夹的路径           #
    # 例如: "C:/Users/YourUser/Documents/MyTxtFiles" #
    # ##################################################

    convert_sjis_to_utf8(sys.argv[1])
