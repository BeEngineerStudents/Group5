from django.db import models

# Create your models here.

class Pokemon(models.Model):
    name = models.CharField(max_length=100, unique=True)  # ポケモン名
    type1 = models.CharField(max_length=50)  # タイプ1
    type2 = models.CharField(max_length=50, blank=True, null=True)  # タイプ2（ない場合も）
    hp = models.IntegerField()  # HP
    attack = models.IntegerField()  # 攻撃
    defense = models.IntegerField()  # 防御
    special_attack = models.IntegerField()  # 特攻
    special_defense = models.IntegerField()  # 特防
    ability = models.CharField(max_length=100, blank=True, null=True)  # 特性
    item = models.CharField(max_length=100, blank=True, null=True)  # 持ち物（任意）

    def __str__(self):
        return self.name

class Move(models.Model):
    name = models.CharField(max_length=100, unique=True)  # 技名
    type = models.CharField(max_length=50)  # 技のタイプ
    category = models.CharField(max_length=50, choices=[("Physical", "物理"), ("Special", "特殊"), ("Status", "変化")])  # 分類
    power = models.IntegerField(blank=True, null=True)  # 威力（変化技はNone）

    def __str__(self):
        return self.name
