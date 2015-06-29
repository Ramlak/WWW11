#########################
###### ZADANIE 2v2 ######
#########################

###  Let's pretend it's py3 compatible
from __future__ import print_function

###  Important imports
from random import randint
from json import dumps, loads
import socket

###  Some global variables ###

global width
global height
global player_step

###  Useful functions

def color(string):
	return "\033[01;32m" + string + "\033[00m"

###  Classes


class Communication(object):
	def bind(self, port):
		port = port if isinstance(port, (int, long)) else int(port)
		for res in socket.getaddrinfo(None, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
			af, socktype, proto, canonname, sa = res
			try:
				s = socket.socket(af, socktype, proto)
			except socket.error as msg:
				s = None
				continue
			try:
				s.bind(sa)
				s.listen(1)
			except socket.error as msg:
				s.close()
				s = None
				continue
			self.s = s
			break

	def accept(self):
		return self.s.accept()

	def send(self, txt):
		return self.s.sendall(txt)

	def sendline(self, txt):
		return self.s.sendall(txt + "\n")

	def recv(self, n):
		return self.s.recv(n)

	def recvuntil(self, delimeter):
		buf = ""
		while not buf.endswith(delimeter):
			buf += self.recv(1)
		return buf

	def recvline(self):
		return self.recvuntil("\n")


class Target(object):
	def __init__(self,city_map, x, y, num):
		self.num = num
		self.city_map = city_map
		self.x = x
		self.y = y
		self.city_map[x][y].append(self)

	def bomb(self, x, y):
		del self.city_map[self.x][self.y][self.city_map[self.x][self.y].index(self)]
		self.x = x
		self.y = y
		self.city_map[x][y].append(self)


class Player(object):
	def __init__(self,city_map, x, y):
		self.city_map = city_map
		self.x = x
		self.y = y
		self.city_map[x][y].append(self)
		#print(str(x) + "," + str(y))

	def move(self, x, y):
		del self.city_map[self.x][self.y][self.city_map[self.x][self.y].index(self)]
		self.x = x
		self.y = y
		self.city_map[x][y].append(self)


class Slaughterhouse(object):
	def __init__(self, num_of_planes):
		self.width = width
		self.height = height
		self.city_map = [[[] for y in range(height)] for x in range(width)]
		self.targets = []
		self.player = None
		self.num_of_planes = num_of_planes
		self.init_city(num_of_planes)
		self.init_player()
		#self.print_it()

	def init_city(self, no_of_planes):
		for i in range(no_of_planes):
			self.targets.append(Target(self.city_map, randint(0, width-1), randint(0, height-1), i))

	def init_player(self):
		while True:
			x, y = randint(0, width-1), randint(0, height-1)
			if len(self.city_map[x][y]) == 0:
				break
		self.player = Player(self.city_map, x, y)

	def move_targets(self):
		for target in self.targets:
			x, y = (target.x + randint(-1, 1)) % width, (target.y + randint(-1,1)) % height  # python modulo is cool :P
			target.bomb(x, y)
			
	def move_player(self, dx, dy):
		if abs(dx) > player_step or abs(dy) > player_step:
			print("Player move to big")
			exit(2)
		self.player.move((self.player.x + dx) % width, (self.player.y + dy) % height)

	def is_dead_already(self):
		return len(self.city_map[self.player.x][self.player.y]) > 1

	def dump(self):
		return dumps({'targets': [[target.x, target.y] for target in self.targets], 'player': [self.player.x, self.player.y]})


	def print_it(self):
		text = " "+"--"*width+"\n"
		total = 0
		image = [[0 for y in range(height)] for x in range(width)]
		for target in self.targets:
			image[target.x][target.y] += 1
		for col in image:
			total += sum(col)
		assert total == self.num_of_planes
		if image[self.player.x][self.player.y] > 0:
			image[self.player.x][self.player.y] = color(":(")
		else:
			image[self.player.x][self.player.y] = color("P ")
		image = zip(*image)
		for col in image:
			text += "|"+"".join(map(lambda x: str(x).ljust(2, " "), col)) + "|\n"
		text += " "+"--"*width+"\n"
		print(text)


if __name__ == '__main__':
	width = 11
	height = 11

	steps_to_survive = 10
	player_step = 2

	total = 0
	### Main loop ###
	round_counter = 1
	srv, cli = Communication(), Communication()
	srv.bind(31415)
	cli.s, addr = srv.accept()
	cli.sendline("CITY:%dx%d" % (width, height))
	while True:
		city = Slaughterhouse(5*round_counter)  ### ;-)
		cli.sendline("ROUND:%d" % round_counter)
		for i in range(1, steps_to_survive + 1):
			cli.sendline("STEP:%d" % i)
			cli.sendline(city.dump())
			# city.print_it()  # for tracing the game/debug
			player_input = loads(cli.recvline().strip())
			city.move_player(*map(int, [player_input['x'], player_input['y']]))
			city.move_targets()		

			if city.is_dead_already():
				cli.sendline("DEAD")
				# city.print_it()  # for tracing the game/debug
				print("Survived %d full rounds" % (round_counter - 1))
				exit(0)
			else:
				cli.sendline("OK")
		round_counter += 1
	