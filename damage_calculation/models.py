from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

class Pokemon(models.Model):
    name = models.CharField(max_length=100, unique=True)  # ポケモン名
    type1 = models.CharField(max_length=50)  # タイプ1
    type2 = models.CharField(max_length=50, blank=True, null=True)  # タイプ2（ない場合も）
    ability = models.CharField(max_length=100, blank=True, null=True)  # 特性
    item = models.CharField(max_length=100, blank=True, null=True)  # 持ち物（任意）

    hp = models.IntegerField()  # HP
    attack = models.IntegerField()  # 攻撃
    defense = models.IntegerField()  # 防御
    special_attack = models.IntegerField()  # 特攻
    special_defense = models.IntegerField()  # 特防

    # 努力値 (EV)
    ev_hp = models.IntegerField(default=0)  # 努力値: HP
    ev_attack = models.IntegerField(default=0)  # 努力値: 攻撃
    ev_defense = models.IntegerField(default=0)  # 努力値: 防御
    ev_special_attack = models.IntegerField(default=0)  # 努力値: 特攻
    ev_special_defense = models.IntegerField(default=0)  # 努力値: 特防
    ev_speed = models.IntegerField(default=0)  # 努力値: 素早さ

    # 個体値 (IV)
    iv_hp = models.IntegerField(default=31)  # 個体値: HP
    iv_attack = models.IntegerField(default=31)  # 個体値: 攻撃
    iv_defense = models.IntegerField(default=31)  # 個体値: 防御
    iv_special_attack = models.IntegerField(default=31)  # 個体値: 特攻
    iv_special_defense = models.IntegerField(default=31)  # 個体値: 特防
    iv_speed = models.IntegerField(default=31)  # 個体値: 素早さ

    def clean(self):
        # 努力値の合計が510を超えていないか確認
        total_ev = (self.ev_hp + self.ev_attack + self.ev_defense + 
                    self.ev_special_attack + self.ev_special_defense + self.ev_speed)
        if total_ev > 510:
            raise ValidationError('努力値の合計は510を超えることができません。')

        # 各ステータスの努力値が252を超えていないか確認
        for ev_field in ['ev_hp', 'ev_attack', 'ev_defense', 'ev_special_attack', 
                        'ev_special_defense', 'ev_speed']:
            ev_value = getattr(self, ev_field)
            if ev_value < 0 or ev_value > 252:
                raise ValidationError(f'{ev_field}は0〜252の範囲で設定する必要があります。')

        # 各個体値が31以下であることを確認
        for iv_field in ['iv_hp', 'iv_attack', 'iv_defense', 'iv_special_attack', 
                         'iv_special_defense', 'iv_speed']:
            if getattr(self, iv_field) < 0 or getattr(self, iv_field) > 31:
                raise ValidationError(f'{iv_field}は0〜31の範囲で設定する必要があります。')

    def __str__(self):
        return self.name


class Move(models.Model):
    name = models.CharField(max_length=100, unique=True)  # 技名
    type = models.CharField(max_length=50)  # 技のタイプ
    category = models.CharField(max_length=50, choices=[("Physical", "物理"), ("Special", "特殊"), ("Status", "変化")])  # 分類
    power = models.IntegerField(blank=True, null=True)  # 威力（変化技はNone）
    
    def __str__(self):
        return self.name


class DamageCalculation(models.Model):
    attacker = models.ForeignKey(Pokemon, related_name="attacker", on_delete=models.CASCADE)  # 攻撃側ポケモン
    defender = models.ForeignKey(Pokemon, related_name="defender", on_delete=models.CASCADE)  # 防御側ポケモン
    move = models.ForeignKey(Move, on_delete=models.CASCADE)  # 使用する技
    level = models.IntegerField(default=50)  # ポケモンのレベル
    weather = models.CharField(max_length=50, blank=True, null=True)  # 天候（例: "晴れ", "雨"）
    terrain = models.CharField(max_length=50, blank=True, null=True)  # 地形（例: "草むら", "砂嵐"）
    is_stab = models.BooleanField(default=False)  # STAB（Same Type Attack Bonus）の適用
    type_effectiveness = models.FloatField(default=1.0)  # タイプ相性補正
    is_critical_hit = models.BooleanField(default=False)  # 急所判定（Trueなら急所ヒット）

    # タイプ相性計算
    def get_type_effectiveness(self):
        type_effectiveness_map = {
            ("Fire", "Grass"): 2.0,
            ("Water", "Fire"): 2.0,
            ("Electric", "Water"): 2.0,
            # 他の相性を追加
        }
        
        effectiveness = 1.0
        if self.attacker.type1 and self.defender.type1:
            effectiveness *= type_effectiveness_map.get((self.move.type, self.defender.type1), 1.0)
        if self.attacker.type2 and self.defender.type2:
            effectiveness *= type_effectiveness_map.get((self.move.type, self.defender.type2), 1.0)
        return effectiveness

    def calculate_damage(self):
        if self.move.power is None:
            return 0  # 威力がない技のダメージは0に設定（変化技など）

        # レベルによる補正
        level_multiplier = (self.level * 2) / 50

        # ダメージの基礎計算
        base_damage = self.move.power  # 技の威力を基準に設定
        
        # 攻撃力、特攻を使用するか判断し、適切なステータスを選択
        if self.move.category == "Physical":
            attack_stat = self.attacker.attack
            defense_stat = self.defender.defense
        else:
            attack_stat = self.attacker.special_attack
            defense_stat = self.defender.special_defense

        # ダメージ計算式
        damage = (base_damage * (attack_stat / defense_stat) * self.get_type_effectiveness() * level_multiplier)

        # STAB補正（同じタイプの技で攻撃した場合のダメージ補正）
        if self.is_stab:
            damage *= 1.5

        # 天候補正
        if self.weather == "晴れ":
            damage *= 1.2  # 火属性技強化
        elif self.weather == "雨":
            damage *= 1.2  # 水属性技強化
        elif self.weather == "砂嵐":
            damage *= 1.2  # 岩タイプの防御強化
        elif self.weather == "霧":
            damage *= 0.75  # 命中率ダウン

        # 急所ヒットの処理
        if self.is_critical_hit:
            # 急所のダメージは通常より1.5倍または2倍になることが多い
            damage *= 1.5  # 1.5倍の補正を加える例

        return damage

    def __str__(self):
        return (f"Damage calculation for {self.attacker.name} (Level: {self.level}, "
                f"HP: {self.attacker.hp}, Attack: {self.attacker.attack}, Special Attack: {self.attacker.special_attack}) vs "
                f"{self.defender.name} (HP: {self.defender.hp}, Defense: {self.defender.defense}, Special Defense: {self.defender.special_defense}) "
                f"using {self.move.name} (Type: {self.move.type}, Power: {self.move.power})")
