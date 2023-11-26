import io
import json
import math
import time
from typing import NamedTuple, Any, Optional

import grpc
import more_itertools
import numpy as np
from PIL import Image

import kockanap_grpc.PdService_pb2_grpc as kockanap

try:
    import xx.kockanap_grpc.PdService_pb2 as kockanap_fake

    type_helper = kockanap_fake
except:
    type_helper = kockanap.kockanap__grpc_dot_PdService__pb2

teamName = 'RBLB'
password = '💡'


def angle_distance(a1: int, a2: int):
    return min(abs(a1 - a2), 360 - abs(a1 - a2))


class Message(NamedTuple):
    type: str
    data: Any

    @staticmethod
    def login():
        return Message('Login', {"teamName": teamName, "password": password})

    @staticmethod
    def buy_bike():
        return Message('BuyBike', {})

    @staticmethod
    def buy_mine(bike_id: int):
        return Message('BuyMine', {"bikeId": bike_id})

    @staticmethod
    def place_mine(bike_id: int):
        return Message('PlaceMine', {"bikeId": bike_id})

    @staticmethod
    def pickup_packet(bike_id: int, packet_id: int):
        return Message('PickupPacket', {"bikeId": bike_id, "packetId": packet_id})

    @staticmethod
    def drop_packet(packet_id: int):
        return Message('DropPacket', {"packetId": packet_id})

    @staticmethod
    def steer_bike(bike_id: int, degree: int, active: bool = True):
        return Message('SteerBike', {"bikeId": bike_id, "isActive": 1 if active else 0, "degree": degree})

    @staticmethod
    def respawn(bike_id: int):
        return Message('RespawnBike', {"bikeId": bike_id})

    def msg(self, counter: int):
        return type_helper.CommandMessage(cmdCounter=counter, commandId=self.type,
                                          commandData=json.dumps(self.data))


class Positioned:
    def __init__(self, X: int, Y: int, **kwargs):
        self.pos = X, Y

    def distance(self, other: 'Positioned') -> int:
        return abs(self.pos[0] - other.pos[0]) + abs(self.pos[1] - other.pos[1])

    def get_rotated(self, angle: int, distance: float) -> 'Positioned':
        cosL = math.cos(angle / 180 * math.pi)
        sinL = math.sin(angle / 180 * math.pi)
        add_angles = abs(cosL) + abs(sinL)
        return Positioned(X=round(self.pos[0] + distance * cosL / add_angles),
                          Y=round(self.pos[1] + distance * sinL / add_angles))

    def get_angle_to(self, pos: 'Positioned') -> int:
        angle = round(math.atan2(self.pos[1] - pos.pos[1], self.pos[0] - pos.pos[0]) / math.pi * 180)
        return angle if angle >= 0 else angle + 360


class Packet(Positioned):
    def __init__(self, Value: int, DestinationX: int, DestinationY: int, OwnerId: int, Id: int,
                 BikeOfPacketId: int, **kwargs):
        super().__init__(**kwargs)
        self.value = Value
        self.target = Positioned(X=DestinationX, Y=DestinationY)
        self.owner = OwnerId
        self.id = Id
        self.bike_id = BikeOfPacketId

    def update(self, **kwargs) -> 'Packet':
        return Packet(**kwargs)


class Bike(Positioned):
    def __init__(self, the_time: float, CurrentMines: int, IsActive: bool, RotDeg: int,
                 PacketInTransportId: int, Id: int,
                 speed: tuple[int, float] = (0, 0.0), **kwargs):
        super().__init__(**kwargs)
        self.id = Id
        self.time = the_time
        self.mines = CurrentMines
        self.is_active = IsActive
        self.rotation = RotDeg
        self.guess_speed = speed
        self.packet_id = PacketInTransportId
        self.rotate_after = 0
        self.changed = True
        self.orig_pos = self.pos
        self.already_steered = False
        self.pick_up_time = time.time() if self.packet_id else None
        self.already_dropped = False
        self.selected_target_id = None
        self.selected_target_time = None
        self.god_help = 0

    def get_pos(self, time: float) -> Positioned:
        if not self.is_active or self.guess_speed[1] == 0.0:
            return self

        speed = self.guess_speed[0] / self.guess_speed[1]
        elapsed_time = time - self.time
        return self.get_rotated(self.rotation, speed * elapsed_time)

    def update(self, time: float, IsActive: bool, own: bool, **kwargs) -> 'Bike':
        speed = self.guess_speed
        if self.is_active and IsActive:
            dist = Positioned(**kwargs).distance(self)
            speed = speed[0] + dist, speed[1] + (time - self.time)

        res = Bike(time, IsActive=IsActive, speed=speed, **kwargs)
        if own:
            res.pick_up_time = self.pick_up_time
            res.selected_target_id = res.selected_target_id or self.selected_target_id
            res.selected_target_time = res.selected_target_time or self.selected_target_time
            res.god_help = self.god_help
            if res.pos == self.orig_pos:
                res.rotate_after = self.rotate_after + round(math.copysign(5, self.rotate_after))
                print("Changed", round(math.copysign(5, self.rotate_after)))
                res.changed = False
            else:
                res.rotate_after = self.rotate_after * (1 if self.changed else -1)
        return res

    def steering(self, angle: int, active: bool = True):
        self.is_active = active
        self.rotation = angle

    def steered(self):
        self.already_steered = True

    def pick_up(self, pick_up_time: float, packet: int):
        self.pick_up_time = pick_up_time
        self.packet_id = packet

    def place_mine(self):
        self.mines -= 1

    def drop_packet(self):
        self.packet_id = 0

    def dropped(self):
        self.already_dropped = True


class Mine(Positioned):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update(self, **kwargs) -> 'Mine':
        return Mine(**kwargs)



class MySolution:
    team_id: int
    arr: np.array

    def optimal_commands(self) -> Message:
        yield Message.login()
        time.sleep(0.005)

        # yield Message.cheat()
        # time.sleep(0.005)

        yield Message.buy_bike()
        time.sleep(0.005)

        while True:
            my_bike: Bike
            if self.money > 1200:
                yield Message.buy_bike()
                time.sleep(0.005)

            for bike_id, my_bike in list(self.bikes[0].items()):
                t = time.time()
                pos = my_bike.get_pos(t)

                was_packet_change = False
                if self.packets and not my_bike.packet_id:
                    packet: Packet
                    packet = next(iter(sorted(self.packets.values(), key=lambda packet: packet.distance(pos))))
                    if packet.distance(pos) < 30:
                        print(f"Pickup packet {bike_id} {packet.id}")
                        my_bike.god_help = 0
                        was_packet_change = True
                        yield Message.pickup_packet(bike_id, packet.id)
                        time.sleep(0.005)
                elif my_bike.packet_id in self.packets and not my_bike.already_dropped:
                    if (self.packets[my_bike.packet_id].target.distance(pos) < 30 or
                        (t - my_bike.pick_up_time) > 80):

                        packet_id = my_bike.packet_id
                        print(f"Drop packet {bike_id} {packet_id}")
                        was_packet_change = True
                        my_bike.dropped()
                        yield Message.drop_packet(packet_id)
                        time.sleep(0.005)

                t = time.time()
                pos = my_bike.get_pos(t)

                if my_bike.mines and self.bikes[1]:
                    bike: Bike
                    bike = next(iter(sorted(self.bikes[1].values(), key=lambda bike: bike.get_pos(t).distance(pos))))
                    if bike.get_pos(t).distance(pos) < 53:
                        print(f"Place mine {bike_id} {my_bike.mines}")
                        yield Message.place_mine(bike_id)
                        time.sleep(0.005)

                if my_bike.mines < 3 and self.money >= 100:
                    yield Message.buy_mine(bike_id)
                    time.sleep(0.005)

                if was_packet_change:
                    print(f"Packet change -> no move")
                    continue

                t = time.time()
                pos = my_bike.get_pos(t)

                angle_dist = []
                for d in range(0, 360):
                    x = 1
                    while True:
                        p = pos.get_rotated(d, x).pos
                        try:
                            if np.min(self.arr[p[1], p[0]]) <= 250:
                                break
                            x += 1
                        except:
                            break
                    angle_dist.append(x)

                angle_avg_dist = {}
                for i, window in enumerate(more_itertools.windowed(angle_dist[:5] + angle_dist + angle_dist[-5:], 11)):
                    angle_avg_dist[i] = np.average(window)

                s = []
                sorted_dirs = sorted(angle_avg_dist.items(), key=lambda l: -l[1])
                for dirs in sorted_dirs:
                    for sx in s:
                        if abs(sx - dirs[0]) < 15:
                            break
                    else:
                        if dirs[1] > 50:
                            s.append(dirs[0])

                if len(s) == 1:
                    for dirs in sorted_dirs:
                        for sx in s:
                            if abs(sx - dirs[0]) < 15:
                                break
                        else:
                            if dirs[1] > 40:
                                s.append(dirs[0])
                s = s[:4]

                print(pos.pos, my_bike.is_active, s, my_bike.guess_speed[0], my_bike.guess_speed[1])

                if not s:
                    prob_dir = sorted_dirs[-1][0] + 180
                    print(f"GOD HELP ME {prob_dir}")

                    if self.respawn > 0 and my_bike.god_help > 50:
                        self.respawn -= 1
                        my_bike.god_help = 0
                        print("God helped respawn")
                        yield Message.respawn(bike_id)
                        time.sleep(0.005)
                        continue

                    my_bike.steered()
                    yield Message.steer_bike(bike_id, prob_dir)
                    time.sleep(0.005)
                    continue

                if not my_bike.is_active or angle_dist[(my_bike.rotation + 360) % 360] < 50 \
                        or angle_dist[(my_bike.rotation + 10 + 360) % 360] < 20 \
                        or angle_dist[(my_bike.rotation - 10 + 360) % 360] < 20 \
                        or angle_dist[(my_bike.rotation + 45 + 360) % 360] < 5 \
                        or angle_dist[(my_bike.rotation - 45 + 360) % 360] < 5 or \
                        len(s) >= 3:

                    if not my_bike.changed:
                        print(f"Stucked {my_bike.rotate_after}")
                        my_bike.steered()
                        yield Message.steer_bike(bike_id, my_bike.rotate_after)
                        time.sleep(0.005)
                        continue

                    if len(s) == 2:
                        d = angle_distance(*s)
                        angle = min(*s) + d // 2
                        if angle_dist[(angle + 180) % 360] < 4:
                            print(f"ANGLE DISTANCE {angle}")
                            my_bike.steered()
                            yield Message.steer_bike(bike_id, angle)
                            time.sleep(0.005)
                            continue

                    target: Optional[Positioned]
                    if my_bike.packet_id in self.packets:
                        target = self.packets[my_bike.packet_id].target
                    else:
                        packet: Packet
                        target = None
                        if (my_bike.selected_target_id in self.packets and not self.packets[my_bike.selected_target_id].bike_id):
                            if t - my_bike.selected_target_time > 60:
                                del self.packets[my_bike.selected_target_id]
                                self.prohibited_package_ids.add(my_bike.selected_target_id)
                                my_bike.selected_target_id = None
                                my_bike.selected_target_time = None
                                if self.respawn > 0:
                                    self.respawn -= 1
                                    print("Remove selected target and respawn")
                                    my_bike.god_help = 0
                                    yield Message.respawn(bike_id)
                                    time.sleep(0.005)
                                    continue
                            else:
                                target = my_bike.selected_target_id

                        if target is None:
                            target = next(iter(sorted(
                                filter(lambda packet: packet.bike_id == 0 and packet.id not in self.already_selected, self.packets.values()),
                                key=lambda packet: packet.distance(pos) + packet.distance(packet.target))), None)
                            if target is not None:
                                self.already_selected.add(target.id)
                                my_bike.selected_target_id = target
                                my_bike.selected_target_time = t

                    reference_dir = my_bike.rotation

                    if target is not None:
                        reference_dir = target.get_angle_to(pos)

                        expected_dir = next(iter(sorted(s, key=lambda l: angle_distance(l, reference_dir))), None)
                        if angle_distance(expected_dir, reference_dir) > 45:
                            it = iter(sorted(s, key=lambda l: angle_distance(l, my_bike.rotation)))
                            expected_dir = next(it, None)
                            """
                            if self.respawn > 0 and my_bike.packet_id in self.packets and (t - (my_bike.pick_up_time or t)) > 40:
                                self.respawn -= 1
                                yield Message.respawn(bike_id)
                                time.sleep(0.005)
                                continue
                            """

                        print(f"Target is {target.pos}, refdir {reference_dir}, expected dir {expected_dir}")
                        if expected_dir is not None:
                            reference_dir = expected_dir

                    print(f"Normal steering to {reference_dir} {my_bike.is_active}")
                    my_bike.steered()
                    yield Message.steer_bike(bike_id, reference_dir)
                    time.sleep(0.005)

            if not self.bikes[0]:
                yield Message.login()
                time.sleep(0.2)

    def commands(self):
        i = 0
        try:
            for command in self.optimal_commands():
                i += 1
                msg = command.msg(i)
                self.send_commands[i] = msg, time.time(), command.data
                yield msg
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"==============================> {e}")

    def start(self):
        for e in self.stub.CommunicateWithStreams(self.commands()):
            if e.cmdCounter == 0:
                data = json.loads(e.commandData)

                now_positions = time.time()
                self.latest_time = now_positions

                old_packets = self.packets
                self.packets = {}
                old_mines = self.mines
                self.mines = {}, {}

                for elem in data:
                    id = elem["Id"]
                    match elem["Type"], elem["OwnerId"]:
                        case "DeliveryBike", self.team_id:
                            self.money = elem["MoneyOfOwnerPlayer"]
                            if id not in self.bikes[0]:
                                self.bikes[0][id] = Bike(now_positions, **elem)
                            else:
                                self.bikes[0][id] = self.bikes[0][id].update(now_positions, own=True, **elem)
                        case "DeliveryBike", _:
                            if id not in self.bikes[1]:
                                self.bikes[1][id] = Bike(now_positions, **elem)
                            else:
                                self.bikes[1][id] = self.bikes[1][id].update(now_positions, own=False, **elem)
                        case "Packet", _:
                            if id not in self.prohibited_package_ids:
                                self.packets[id] = Packet(**elem) if id not in old_packets else old_packets[id].update(
                                    **elem)
                        case "Mine", self.team_id:
                            if id not in old_mines[0]:
                                self.mines[0][id] = Mine(**elem)
                            else:
                                self.mines[0][id] = old_mines[0][id].update(**elem)
                        case "Mine", _:
                            if id not in old_mines[1]:
                                self.mines[1][id] = Mine(**elem)
                            else:
                                self.mines[1][id] = old_mines[1][id].update(**elem)
                        case _, _:
                            raise RuntimeError(f"Unhandled type {elem['Type']}, {elem}")
            else:
                sent_command, timed, data = self.send_commands.pop(e.cmdCounter)
                if e.commandId == 'LoginResponse' or sent_command.commandId == 'BuyBike' or sent_command.commandId == 'BuyMine':
                    pass
                elif e.commandData == 'OK' and sent_command.commandId == 'SteerBike':
                    print("Steering applied")
                    self.bikes[0][data['bikeId']].steering(data['degree'], data['isActive'])
                elif e.commandData == 'OK' and sent_command.commandId == 'PickupPacket':
                    self.bikes[0][data['bikeId']].pick_up(time.time(), data['packetId'])
                elif e.commandData == 'OK' and sent_command.commandId == 'DropPacket':
                    self.prohibited_package_ids.add(data['packetId'])
                    if data['packetId'] in self.packets:
                        bike_id = self.packets[data['packetId']].bike_id
                        del self.packets[data['packetId']]
                        self.bikes[0][bike_id].drop_packet()
                else:
                    if sent_command.commandId == 'PlaceMine':
                        self.bikes[0][data['bikeId']].place_mine()

                    print(f"Got response [{e.cmdCounter} {sent_command.commandId}] {e.commandId} after {time.time() - timed} time {e.commandData}")

    def __init__(self, stub):
        def register():
            with open('Robot-2-icon2.png', mode='rb') as file:
                image = file.read()

            response = self.stub.RegisterTeam(
                type_helper.RegistrationRequestMessage(teamName=teamName, teamPassword=password, teamImagePng=image))

            self.team_id = response.teamId
            with open('map.png', mode='wb') as ofile:
                ofile.write(response.mapImagePng)
                self.arr = np.asfortranarray(Image.open(io.BytesIO(response.mapImagePng)))

        self.respawn = 3
        self.latest_time = time.time()
        self.money = 100
        self.send_commands = {}
        self.prohibited_package_ids = set()
        self.already_selected = set()
        self.bikes = {}, {}
        self.packets = {}
        self.mines = {}, {}
        self.stub = stub
        register()
        self.start()


with grpc.insecure_channel('10.8.9.121:9080', options=[
    ("grpc.http2.max_pings_without_data", 0),
    ("grpc.keepalive_permit_without_calls", 1),
    ("grpc.keepalive_time_ms", 10000),
]) as channel:
    MySolution(kockanap.PdServiceStub(channel))
