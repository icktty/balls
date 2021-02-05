from scene import *
from math import pi, sin, cos, atan2, radians, sqrt
from random import random, uniform, choice

A = Action

class Player (SpriteNode):
  def __init__(self, **kwargs):
    SpriteNode.__init__(self, 'spc:PlayerShip3Green', **kwargs)
    self.size = (64, 64)

class Item (SpriteNode):
  def __init__(self, img, **kwargs):
    SpriteNode.__init__(self, img, **kwargs)
    self._amount = Point(0, 0)

  def create(self, pos, size, r, v):
    self.position = pos
    self.size = (size, size)
    self._amount = Point(cos(r) * v, sin(r) * v)    

  def update(self):
    self.position += self._amount

class Ball (Item):
  def __init__(self, **kwargs):
    Item.__init__(self, 'shp:wavering', **kwargs)

  def create(self, pos, size):
    v = uniform(2, 6)
    r = radians(uniform(0, 360))
    Item.create(self, pos, size, r, v)

  def update(self):
    Item.update(self)
    pos = self.position
    if pos.x <= 0 or pos.x >= self.parent.size.w:
      self._amount.x = -self._amount.x
      self.position = (pos.x + self._amount.x, pos.y)
    if pos.y <= self.parent.size.h / 3 or pos.y >= self.parent.size.h:
      self._amount.y = -self._amount.y
      self.position = (pos.x, pos.y + self._amount.y)

class Shot (Item):
  def __init__(self, **kwargs):
    Item.__init__(self, 'shp:Circle', **kwargs)
    self.__out = False
    self.__ignore_balls = []
    self.__mine = False

  def create(self, pos, r, v):
    Item.create(self, pos, 16, r, v)

  def is_out(self):
    return self.__out

  def get_ignore_balls(self):
    return self.__ignore_balls

  def set_ignore_balls(self, balls):
    self.__ignore_balls = balls

  def is_ignore_ball(self, ball):
    return ball in self.__ignore_balls

  def is_mine(self):
    return self.__mine

  def set_mine(self):
    self.__mine = True

  def update(self):
    Item.update(self)
    pos = self.position
    if self.position.x <= 0 \
    or self.position.x >= self.parent.size.w \
    or self.position.y <= 0 \
    or self.position.y >= self.parent.size.h:
      self.__out = True

  def get_velocity(self):
    return sqrt(self._amount.x ** 2 + self._amount.y ** 2)

class Game (Scene):
  def setup(self):
    self.balls = []
    self.shots = []
    self.rests = []
    self.player = Player(parent = self)
    self.score_label = LabelNode(parent = self)
    self.score_label.anchor_point = Point(0, 1)
    self.score_label.position = (8, self.size.h - 8)
    self.score_label.font = ('<System-Bold>', 24)
    self.clear_stage_flag = False
    self.start_game()

  def update(self):
    self.flow_star()
    if self.clear_stage_flag:
      return
    if len(self.balls) == 0 and len(self.shots) == 0:
      self.clear_stage()
      return      
    for ball in list(self.balls):
      ball.update()
    for shot in list(self.shots):
      shot.update()
      if shot.is_out():
        self.shot_out(shot)
        return
      self.shot_hittest(shot)

  def touch_began(self, touch):
    if self.player.frame.contains_point(touch.location):
      self.last_touch_pos = touch.location
      self.before_time = self.t
      self.player.position = (touch.location.x, 80)
      
  def touch_moved(self, touch):
    if self.last_touch_pos == Point(-1, -1):
      return
    if self.player.frame.contains_point(touch.location):
      self.last_touch_pos = touch.location
      self.before_time = self.t
      self.player.position = (touch.location.x, 80)

  def touch_ended(self, touch):
    if self.last_touch_pos != Point(-1, -1):
      t = self.t - self.before_time
      if t > 0.5:
        return
      vv = (touch.location - self.last_touch_pos) / (120 * t)      
      if vv.y <= 0:
        return
      if abs(vv.x) > vv.y:
        return
      v = sqrt(vv.x ** 2 + vv.y ** 2)
      if v < 8 or v > 24:
        return
      r = atan2(vv.y, vv.x)
      pos = Point(self.player.position.x, 96)
      shot = self.shot_create(pos, r, v)
      shot.set_mine()
      self.shot_count += 1
      self.last_touch_pos = Point(-1, -1)

  def start_game(self):
    for ball in list(self.balls):
      ball.remove_from_parent()
    self.balls = []
    self.last_touch_pos = Point(-1, -1)
    self.before_time = self.t
    self.rest_num = 3
    self.score = 0
    self.stage = 1
    self.start_stage()

  def start_stage(self):
    self.shot_count = 0
    self.hit_count = 0
    self.show_score()
    self.start_player()
    ball_size = self.stage * 16 + 48
    if ball_size > 96:
      ball_size = 96 
    ball_num = self.stage - 6
    if ball_num < 1:
      ball_num = 1
    for i in range(ball_num):
      ball = self.ball_create(Point(self.size.w / 2, self.size.h - 100), ball_size)
    self.present_modal_scene(ReadyScene(self.stage))

  def start_player(self):
    self.show_rest()
    self.player.position = (self.size.w / 2, -32)
    self.player.run_action(A.move_by(0, 112, 1))

  def show_score(self):
    self.score_label.text = 'SCORE ' + str(self.score)

  def show_rest(self):
    if len(self.rests) > 0:
      for rest in list(self.rests):
        rest.remove_from_parent()
      self.rests = []
    if self.rest_num > 1:
      for i in range(self.rest_num - 1):
        rest = SpriteNode(self.player.texture, parent = self)
        rest.size = (32, 32)
        rest.anchor_point = (0, 0)
        rest.position = (i * 36 + 8, 8)
        self.add_child(rest)
        self.rests.append(rest)        

  def shot_out(self, shot):
    self.shot_remove(shot) 
    if shot.is_mine() == False:
      return
    ball_size = 16 * (self.stage - 1)
    if ball_size < 48:
      return
    if ball_size > 96:
      ball_size = 96
    pos = shot.position
    if pos.y <= 0:
      return
    elif pos.y >= self.size.h:
      pos = Point(pos.x, self.size.h - 1)
    if(pos.x <= 0):
      pos = Point(1, pos.y)
    elif pos.x >= self.size.w:
      pos = Point(self.size.w - 1, pos.y)
    self.ball_create(pos, ball_size)

  def shot_hittest(self, shot):
    for ball in list(self.balls):
      if shot.is_ignore_ball(ball):
        continue
      if ball.frame.intersects(shot.frame):
        self.ball_remove(ball)
        self.shot_remove(shot)
        new_balls = []
        if ball.size[0] >= 64:
          for cnt in range(2):
            new_balls.append(self.ball_create(ball.position, ball.size[0] - 16))
          v = shot.get_velocity()
          r = random() * pi
          for i in range(3):
            new_shot = self.shot_create(ball.position, r, v)
            new_shot.set_ignore_balls(shot.get_ignore_balls() + new_balls)
            r += pi / 3 * 2
        if shot.is_mine():
          self.hit_count += 1
        self.score += 1
        self.show_score()
        return
    if shot.is_mine() == False:
      if self.player.frame.intersects(shot.frame):
        self.shot_remove(shot)
        self.miss()

  def shot_create(self, pos, r, v):
    shot = Shot(parent = self)
    shot.create(pos, r, v)
    self.add_child(shot)
    self.shots.append(shot)
    return shot

  def shot_remove(self, shot):
    self.shots.remove(shot)
    shot.remove_from_parent()

  def ball_create(self, pos, size):
    ball = Ball(parent = self)
    ball.create(pos = pos, size = size)
    self.add_child(ball)
    self.balls.append(ball)
    return ball

  def ball_remove(self, ball):
    self.balls.remove(ball)
    ball.remove_from_parent()
    dis = SpriteNode(ball.texture, parent = self)
    dis.position = ball.position
    dis.size = ball.size
    dis.run_action(A.sequence( \
                      A.group( \
                        A.fade_to(0, 0.1), \
                        A.scale_to(1.5, 0.1) \
                      ), \
                      A.remove() ))

  def miss(self):
    self.rest_num -= 1
    (x, y) = self.player.position;
    self.player.position = (x, -64)
    for i in range(32):
      dx = uniform(-32, 32)
      dy = uniform(-32, 32)
      s = uniform(32, 64)
      t = int(uniform(0, 8))
      texture = 'shp:Explosion0' + str(t)
      explosion = SpriteNode(texture, parent = self)
      explosion.position = (x + dx, y + dy)
      explosion.size = (s, s)
      explosion.run_action(A.sequence( \
                              A.scale_to(0, 0), \
                              A.wait(random()), \
                              A.scale_to(1, 0.5), \
                              A.scale_to(0, 0.5), \
                              A.remove() ))
    self.run_action(A.sequence(A.wait(3), A.call(self.wait_after_miss)))

  def wait_after_miss(self):
    if len(self.shots) > 0:
      self.run_action(A.sequence(A.wait(1), A.call(self.wait_after_miss)))       
    else:
      if self.rest_num > 0:
        self.start_player()
      else:
        self.game_over()

  def game_over(self):
    self.present_modal_scene(GameOverScene())
    self.run_action(A.call(self.wait_after_game_over))

  def wait_after_game_over(self):
    if type(self.presented_scene) is GameOverScene:
      self.run_action(A.sequence(A.wait(1), A.call(self.wait_after_game_over)))       
    else:
      self.rest_num = 3
      self.start_game()

  def clear_stage(self):
    self.clear_stage_flag = True
    self.player.run_action(A.sequence( \
                              A.wait(2), \
                              A.move_by(0, self.size.h, 1, TIMING_EASE_IN_2) ))
    self.present_modal_scene(ClearStageScene(self))

  def after_clear_stage(self):
    self.stage += 1
    self.start_stage()
    self.clear_stage_flag = False

  def flow_star(self):
    if int(random() * 6) != 0:
      return
    star = SpriteNode(parent = self)
    star.z_position = -1
    star.position = (uniform(0, self.size.w), self.size.h)
    star.size = (2, 2)
    r = choice([0.5, 1.0])
    g = choice([0.5, 1.0])
    b = choice([0.5, 1.0])
    star.color = (r, g, b)

    star.run_action(A.sequence( \
                      A.move_by(0, -self.size.h, uniform(1, 3)),
                      A.remove() ))

class ReadyScene (Scene):
  def __init__(self, stage):
    Scene.__init__(self)
    self.stage = stage

  def setup(self):
    self.label = LabelNode(parent = self)
    self.label.position = (self.size.w / 2, self.size.h / 2)
    self.label.font = ('<System-Bold>', 32)
    self.label.text = 'STAGE ' + str(self.stage)
    self.run_action(A.sequence( \
                      A.repeat( \
                        A.sequence( \
                          A.scale_to(0, 0), \
                          A.wait(0.5), \
                          A.scale_to(1, 0), \
                          A.wait(0.5) ), \
                        3), \
                      A.call(self.end) ))

  def end(self):
    self.dismiss_modal_scene()

class GameOverScene (Scene):
  def setup(self):
    self.label1 = LabelNode(parent = self)
    self.label1.position = (self.size.w / 2, self.size.h / 2)
    self.label1.font = ('<System-Bold>', 32)
    self.label1.text = 'GAME OVER'  
    self.label2 = LabelNode(parent = self)
    self.label2.position = (self.size.w / 2, self.size.h / 2 - 48)
    self.label2.font = ('<System-Bold>', 24)
    self.label2.text = 'TOUCH TO NEW GAME'  

  def touch_ended(self, touch):
    self.dismiss_modal_scene()

class ClearStageScene (Scene):
  def __init__(self, main_scene):
    Scene.__init__(self)
    self.main_scene = main_scene

  def setup(self):
    self.labels = [None, None, None, None, None, None]
    self.pos_y = [48, 0, -32, -64, -96, -128]
    self.font_size = [32, 24, 24, 24, 24, 24]
    stage = self.main_scene.stage
    shot_count = self.main_scene.shot_count
    hit_count = self.main_scene.hit_count
    ratio = round(hit_count / shot_count * 100, 1)
    self.bonus = int(ratio * 10)
    if ratio == 100:
      self.bonus = 2000
    self.text = ['STAGE ' + str(stage) + ' CLEAR', \
                 '<RESULT>', \
                 str(shot_count) + ' SHOTS', \
                 str(hit_count) + ' HITS', \
                 'RATIO ' + str(ratio) + '%', \
                 '']
    self.start_t = self.t

  def update(self):
    dt = self.t - self.start_t
    for i in range(6):
      if dt > i + 1 and self.labels[i] == None:
        self.labels[i] = LabelNode(parent = self)
        self.labels[i].position = (self.size.w / 2, \
                                   self.size.h / 2 + self.pos_y[i])
        self.labels[i].font = ('<System-Bold>', self.font_size[i])
        self.labels[i].text = self.text[i]
    if dt > 6 and self.labels[5].text == '':
      self.show_bonus()
    if dt > 7 and dt < 10:
      if self.bonus > 0:
        self.main_scene.score += 1
        self.main_scene.show_score()
        self.bonus -= 1
        self.show_bonus()
    if dt > 10:
      if self.bonus > 0:
        self.main_scene.score += self.bonus
        self.main_scene.show_score()
        self.bonus = 0
        self.show_bonus()
    if dt > 11:
      self.dismiss_modal_scene()
      self.main_scene.after_clear_stage()

  def show_bonus(self):
    self.labels[5].text = 'BONUS ' + str(self.bonus)

if __name__ == '__main__':
  run(Game(), PORTRAIT, show_fps=True)
