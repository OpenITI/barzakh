from openiti.helper.ara import normalize_composites

allah = normalize_composites("ﷲ")
print(len(allah))

a = normalize_composites("أ")
print(len(a))

with open("0730ShaficIbnCali.HusnManaqib.LMN20200820-ara1.completed",
          mode="r", encoding="utf-8") as file:
    text = file.read()
print(len(text))
text = normalize_composites(text)
print(len(text))
with open("0730ShaficIbnCali.HusnManaqib.LMN20200820-ara1.completed",
          mode="w", encoding="utf-8") as file:
    file.write(text)

