

def write(path, value):
    # 以添加的形式写入csv，跟处理txt文件一样，设定关键字"a"，表追加
    csvFile = open(path, "a")

    # 新建对象writer
    writer = csv.writer(csvFile)
    writer.writerow(value)

    csvFile.close()



