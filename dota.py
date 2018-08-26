import requests, json
from io import BytesIO
from urllib.request import urlopen
import xlsxwriter
import copy


# item 指radiant 或dire 的bans、picks列表数据
def bp(item, bp_dict):
    if item is None:
        return
    # 遍历bans 或picks 数据
    for i, bp in enumerate(item):
        key = bp["name"]
        # 如果这个英雄已存在，count+1
        if key in bp_dict.keys():
            bp_dict[key]["count"] = bp_dict[key]["count"] + 1
        else:  # 不存在就记录一条数据
            bp_dict[key] = copy.deepcopy(bp)
            bp_dict[key].update(count=1)
    return bp_dict


def dota():
    bp_dict = dict()
    b_dict = dict()
    p_dict = dict()
    page = 1
    while True:
        url = "https://www.dotamore.com/api/v1/league/matchlist?league_id=9870&page=%d&size=20" % page
        response = requests.get(url)
        data = json.loads(response.text)
        page += 1
        for item in data["data"]:
            # 比赛从8月16开始，小于这个时间生成excel，跳出循环
            if item["end_time"] < "2018-08-16 00:00":
                # x[0]是根据键排序，x[1]是根据值，这里的值是字典，取["count"]项排序，得到的是元祖的list
                new_b_list = sorted(b_dict.items(), key=lambda x: x[1]["count"], reverse=True)
                new_p_list = sorted(p_dict.items(), key=lambda x: x[1]["count"], reverse=True)
                new_bp_list = sorted(bp_dict.items(), key=lambda x: x[1]["count"], reverse=True)
                create_excel(new_b_list, new_p_list, new_bp_list)
                return
            # ban的数据
            bp(item["radiant"]["bans"], b_dict)
            bp(item["dire"]["bans"], b_dict)
            # pick的数据
            bp(item["radiant"]["picks"], p_dict)
            bp(item["dire"]["picks"], p_dict)

            bp(item["radiant"]["bans"], bp_dict)
            bp(item["radiant"]["picks"], bp_dict)
            bp(item["dire"]["bans"], bp_dict)
            bp(item["dire"]["picks"], bp_dict)

def create_excel(b_list, p_list, bp_list):
    # 创建excel表格
    file = xlsxwriter.Workbook("dota.xlsx")
    # 创建工作表1
    sheet1 = file.add_worksheet("sheet1")
    # 创建表头
    headers = ["图片", "英雄", "ban", "", "图片", "英雄", "pick", "", "图片", "英雄", "bp_all"]
    for i, header in enumerate(headers):
        # 第一行为表头
        sheet1.write(0, i, header)

    insert_data(sheet1, headers, b_list, 0, 1, 2)
    insert_data(sheet1, headers, p_list, 4, 5, 6)
    insert_data(sheet1, headers, bp_list, 8, 9, 10)

    insert_chart(file, sheet1, b_list, "b_list", "M2", 1, 2)
    insert_chart(file, sheet1, p_list, "p_list", "M13", 5, 6)
    insert_chart(file, sheet1, bp_list, "bp_list", "M24", 9, 10)

    # 关闭表格
    file.close()


def insert_data(sheet1, headers, bp_list, col1, col2, col3):
    for row in range(len(bp_list)):  # 行
        # 设置行高
        sheet1.set_row(row + 1, 30)
        for col in range(len(headers)):  # 列
            if col == col1:  # 英雄图片，根据id获取
                url = "http://cdn.dotamore.com/heros_id_62_35/%d.png" % bp_list[row][1]["id"]
                image_data = BytesIO(urlopen(url).read())
                sheet1.insert_image(row + 1, col, url, {"image_data": image_data})
            if col == col2:  # 英雄名
                name = bp_list[row][1]["name_cn"]
                sheet1.write(row + 1, col, name)
            if col == col3:  # 统计次数
                count = bp_list[row][1]["count"]
                sheet1.write(row + 1, col, count)


# 插入柱状图
def insert_chart(file, sheet1, bp_list, name, M, col_x, col_y):
    chart = file.add_chart({"type": "column"})  # 柱状图
    chart.add_series({
        "categories": ["sheet1", 1, col_x, len(bp_list), col_x],  # 图表类别标签范围，x轴，这里取英雄的名字，即英雄名字那一列，行数根据数据列表确定
        "values": ["sheet1", 1, col_y, len(bp_list), col_y],  # 图表数据范围，y轴，即次数那一列，行数根据数据列表确定
        "data_labels": {"value": True},
    })
    chart.set_title({"name": name})  # 图表标题
    chart.set_size({"width": 2000, "height": 400})
    chart.set_x_axis({'name': '英雄'})  # x轴描述
    chart.set_y_axis({'name': '次数'})  # y轴描述
    chart.set_style(3)  # 直方图类型
    sheet1.insert_chart(M, chart)  # 在表格M处插入柱状图


dota()
