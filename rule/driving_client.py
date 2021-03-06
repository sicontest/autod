from numba import prange

from drive_controller import DrivingController
import numpy as np
import math


class DrivingClient(DrivingController):
    def __init__(self):
        # =========================================================== #
        #  Area for member variables =============================== #
        # =========================================================== #
        # Editing area starts from here
        #

        self.is_debug = False
        self.collision_flag = True
        self.collision_count = 0
        self.prev_to_middle = 0.0
        self.before_collision_throttle = 1
        self.full_throttling = True
        self.emergency_braking = False
        self.marina_emergency = False

        self.is_like_rect = False

        self.set_steering = 0.0
        self.set_throttle = 1.0
        self.set_brake = 0.0

        self.steering_by_middle = 0.0
        self.steering_by_angle = 0.0

        self.is_opponent_close = False
        #
        # Editing area ends
        # ==========================================================#
        super().__init__()

    def control_driving(self, car_controls, sensing_info):

        # =========================================================== #
        # Area for writing code about driving rule ================= #
        # =========================================================== #
        # Editing area starts from here
        #

        if self.is_debug:
            print("=========================================================")
            print("to middle: {}".format(sensing_info.to_middle))

            print("collided: {}".format(sensing_info.collided))
            print("car speed: {} km/h".format(sensing_info.speed))

            print("is moving forward: {}".format(sensing_info.moving_forward))
            print("moving angle: {}".format(sensing_info.moving_angle))
            print("lap_progress: {}".format(sensing_info.lap_progress))

            print("track_forward_angles: {}".format(sensing_info.track_forward_angles))
            print("track_forward_obstacles: {}".format(sensing_info.track_forward_obstacles))
            print("opponent_cars_info: {}".format(sensing_info.opponent_cars_info))
            print("distance_to_way_points: {}".format(sensing_info.distance_to_way_points))
            print("=========================================================")

        ###########################################################################
        # print("collided: {}".format(sensing_info.collided))
        # Moving straight forward

        self.prev_to_middle = abs(sensing_info.to_middle)

        self.set_steering = 0.0
        self.set_throttle = 1.0
        self.set_brake = 0.0

        self.set_steering_with_no_obstacles(sensing_info)

        if sensing_info.speed > 120:
            dist = 80
        else:
            dist = 50
        if len(sensing_info.track_forward_obstacles) > 0 and sensing_info.track_forward_obstacles[0]['dist'] < dist:
            self.set_steering_with_obstacles(sensing_info)

        self.set_steering = self.steering_by_angle + self.steering_by_middle

        if abs(sensing_info.to_middle) > (self.half_road_limit - 3):
            if self.set_steering > 0:
                if sensing_info.to_middle < 0:
                    self.set_steering += 0.1
                else:
                    self.set_steering += -0.1
            else:
                if sensing_info.to_middle < 0:
                    self.set_steering += -0.1
                else:
                    self.set_steering += 0.1

        if abs(self.set_steering) > 1:
            if self.set_steering > 0:
                self.set_steering = 1
            else:
                self.set_steering = -1

        if len(sensing_info.opponent_cars_info) > 0 and abs(sensing_info.opponent_cars_info[0]['dist']) < 4:
            self.is_opponent_close = True
        else:
            self.is_opponent_close = False

        if sensing_info.collided and self.collision_count == 0 and (
                not self.is_opponent_close or sensing_info.speed < 10):
            self.collision_count = 6
            self.before_collision_throttle *= -1
            self.set_throttle = self.before_collision_throttle
            self.set_brake = 0.0
            if self.before_collision_throttle < 0:
                if sensing_info.moving_angle > 0:
                    self.set_steering = 0.8
                else:
                    self.set_steering = -0.8
            else:
                if sensing_info.moving_angle > 0:
                    self.set_steering = -0.8
                else:
                    self.set_steering = 0.8
        elif self.collision_count > 0 and sensing_info.speed < 10:
            self.collision_count -= 1
            self.set_throttle = self.before_collision_throttle
            self.set_brake = 0.0
            if self.before_collision_throttle < 0:
                if sensing_info.moving_angle > 0:
                    self.set_steering = 0.8
                else:
                    self.set_steering = -0.8
            else:
                if sensing_info.moving_angle > 0:
                    self.set_steering = -0.8
                else:
                    self.set_steering = 0.8
        else:
            self.collision_count = 0
            if sensing_info.moving_forward and abs(sensing_info.moving_angle) < 90:
                self.before_collision_throttle = 1
            elif sensing_info.moving_forward and abs(sensing_info.moving_angle) >= 90:
                self.before_collision_throttle = -1
            elif (not sensing_info.moving_forward) and abs(sensing_info.moving_angle) < 90:
                self.before_collision_throttle = -1
            else:
                self.before_collision_throttle = 1

        if not sensing_info.moving_forward and self.collision_count == 0 and sensing_info.speed > 0:
            self.set_steering = -1.0

        #if sensing_info.speed > 140:
        #    self.set_throttle = 0.2
        #    self.set_brake = 0.5

        car_controls.steering = self.set_steering
        car_controls.throttle = self.set_throttle
        car_controls.brake = self.set_brake

        # print("steering:{}, throttle:{}, brake:{}".format(car_controls.steering, car_controls.throttle, car_controls.brake))
        # print(sensing_info.track_forward_angles)
        # print(np.max(sensing_info.track_forward_angles))
        # print(np.std(sensing_info.track_forward_angles))
        # print(sensing_info.speed)
        # print(sensing_info.track_forward_obstacles)
        if self.is_debug:
            print("steering:{}, throttle:{}, brake:{}".format(car_controls.steering, car_controls.throttle,
                                                              car_controls.brake))
        #
        # Editing area ends
        # ==========================================================#
        return car_controls

    # ============================
    # If you have NOT changed the <settings.json> file
    # ===> player_name = ""
    #
    # If you changed the <settings.json> file
    # ===> player_name = "My car name" (specified in the json file)  ex) Car1
    # ============================
    def set_player_name(self):
        player_name = "Car1"
        return player_name

    def set_steering_with_no_obstacles(self, sensing_info):
        road_ran = 3
        ang = 120
        ang_num = 1

        if sensing_info.speed > 140:
            road_ran = 10
            ang = 75
            ang_num = 4
            if not self.full_throttling:
                ang_num = 3
        elif sensing_info.speed > 110:
            road_ran = 9
            ang = 85
            ang_num = 3
            if not self.full_throttling:
                ang_num = 2
        elif sensing_info.speed > 80:
            road_ran = 6
            ang = 95
            ang_num = 2
        elif sensing_info.speed > 50:
            road_ran = 3
            ang = 120
            ang_num = 1

        # set_throttle = 1.0
        # set_brake = 0.0

        # if self.marina_emergency:
        #    ang_num += 2

        self.steering_by_angle = (sensing_info.track_forward_angles[ang_num] - sensing_info.moving_angle) / ang
        self.steering_by_middle = (sensing_info.to_middle / 50) * -1
        # self.set_steering += self.steering_by_middle

        full_throttle = True
        emergency_brake = False
        is_emergency_direction_right = True
        emergency_start_index = 0

        for i in range(road_ran):
            f_road = abs(sensing_info.track_forward_angles[i])
            # print(f_road)
            if f_road > 50:
                full_throttle = False
            if f_road > 89:
                if sensing_info.track_forward_angles[i] < 0:
                    is_emergency_direction_right = False
                emergency_brake = True
                break

        self.is_like_rect = False
        ang_diffs = []

        for i in range(1, 10):
            ang_diff = abs(sensing_info.track_forward_angles[i] - sensing_info.track_forward_angles[i - 1])
            ang_diffs.append(ang_diff)
            if ang_diff > 30:
                self.is_like_rect = True

        self.full_throttling = full_throttle
        self.emergency_braking = emergency_brake
        self.marina_emergency = False

        absolute_angles = np.absolute(sensing_info.track_forward_angles)

        if not full_throttle:
            if sensing_info.speed > 130:
                self.set_throttle = 0.5
            if sensing_info.speed > 120:
                self.set_brake = 0.3
            """
            if np.max(sensing_info.track_forward_angles) > 50:
                self.steering_by_middle = ((sensing_info.to_middle-(self.half_road_limit/5)) / 50) * -1
            else:
                self.steering_by_middle = ((sensing_info.to_middle+(self.half_road_limit/5)) / 50) * -1
            """
            """
            if np.std(sensing_info.track_forward_angles) > 28 and 90 > np.max(absolute_angles) and sensing_info.speed > 30:
                self.marina_emergency = True
                self.set_brake = 1.0
                self.set_throttle = 0.2
                if np.max(sensing_info.track_forward_angles) > 50:
                    self.steering_by_angle = self.steering_by_angle + 0.1
                else:
                    self.steering_by_angle = self.steering_by_angle - 0.1
            """
        if emergency_brake:
            self.set_throttle = 0.7
            if np.std(sensing_info.track_forward_angles) > 25 and sensing_info.speed > 30:
                self.set_brake = 0.3
                """
                if is_emergency_direction_right:
                    self.steering_by_angle += (((self.half_road_limit / 2) / 20) * -1)
                else:
                    self.steering_by_angle += ((self.half_road_limit / 2) / 20)
                """
            else:
                if np.max(sensing_info.track_forward_angles) > 50:
                    self.steering_by_angle = self.steering_by_angle + 0.3
                else:
                    self.steering_by_angle = self.steering_by_angle - 0.3

        ang_diffs_std = np.std(ang_diffs)
        # print(ang_diffs_std)
        if self.is_like_rect and (not emergency_brake) and (
                (120 > np.max(absolute_angles) > 84 and ang_diffs_std > 9.5) or ang_diffs_std > 13):
            # print("is lect")
            # print(sensing_info.track_forward_angles)
            # print(np.std(ang_diffs))
            if sensing_info.speed > 120:
                self.set_brake = 1.0
                self.set_throttle = 0.0
            elif sensing_info.speed > 90:
                self.set_brake = 1.0
                self.set_throttle = 0.2

    def set_steering_with_obstacles(self, sensing_info):
        # print("-------------set_steering_with_obstacles----------------")
        to_middle = sensing_info.to_middle

        obs_to_mid = sensing_info.track_forward_obstacles[0]['to_middle']
        diff = (to_middle - obs_to_mid)
        obs_dist = sensing_info.track_forward_obstacles[0]['dist']
        target_selected = False
        target = 0.0

        # if len(sensing_info.track_forward_obstacles) > 1:
        # print(sensing_info.track_forward_obstacles[1]['dist'] - obs_dist)

        if abs(diff) < 4 or (abs(obs_to_mid) < 3.5 and obs_to_mid != -2.51 and obs_to_mid != 2.99):
            to_be_target = [obs_to_mid - 5, obs_to_mid + 5]

            # print("target to be selected")
            """
            for i in range(2):
                if abs(to_be_target[i]) > (self.half_road_limit-1.25):
                    target = to_be_target[1-i]
                    target_selected = True
                    break
            """
            if not target_selected:
                if len(sensing_info.opponent_cars_info) > 0 and abs(sensing_info.opponent_cars_info[0]['dist']) < 5:
                    opponent_tomiddle = sensing_info.opponent_cars_info[0]['to_middle']
                    if abs(to_be_target[0] - opponent_tomiddle) < abs(to_be_target[0] - to_middle):
                        target = to_be_target[1]
                        target_selected = True
                    else:
                        target = to_be_target[0]
                        target_selected = True
            """
            if not target_selected:
                if len(sensing_info.track_forward_obstacles) > 1 and 30 >(sensing_info.track_forward_obstacles[1]['dist'] - obs_dist) > 10 and (sensing_info.track_forward_obstacles[1]['to_middle'] - obs_to_mid) < 5.7:
                    if (sensing_info.track_forward_obstacles[1]['to_middle'] - obs_to_mid) * (to_be_target[0] - obs_to_mid) > 0:
                        target = to_be_target[1]
                        target_selected = True
                    elif (sensing_info.track_forward_obstacles[1]['to_middle'] - obs_to_mid) * (to_be_target[0] - obs_to_mid) < 0:
                        target = to_be_target[0]
                        target_selected = True
            """

            if not target_selected:
                if abs(to_be_target[0] - to_middle) < abs(to_be_target[1] - to_middle):
                    target = to_be_target[0]
                    target_selected = True
                else:
                    target = to_be_target[1]
                    target_selected = True

        elif len(sensing_info.track_forward_obstacles) > 1 and (
                (sensing_info.track_forward_obstacles[1]['dist'] - obs_dist) < 30 or
                sensing_info.track_forward_obstacles[1]['dist'] < 60):
            second_obs_tomiddle = sensing_info.track_forward_obstacles[1]['to_middle']
            if abs(second_obs_tomiddle - sensing_info.to_middle) < 4:
                to_be_target = [second_obs_tomiddle - 5, second_obs_tomiddle + 5]

                for i in range(2):
                    if abs(to_be_target[i]) > (self.half_road_limit - 1.25):
                        target = to_be_target[1 - i]
                        target_selected = True
                        break
                    if (to_be_target[i] - second_obs_tomiddle) * (
                            sensing_info.track_forward_obstacles[0]['to_middle'] - second_obs_tomiddle) > 0:
                        if abs((to_be_target[i] - second_obs_tomiddle)) > abs(
                                sensing_info.track_forward_obstacles[0]['to_middle'] - second_obs_tomiddle):
                            target = to_be_target[1 - i]
                            target_selected = True
                            break

                if not target_selected:
                    if len(sensing_info.opponent_cars_info) > 0 and abs(sensing_info.opponent_cars_info[0]['dist']) < 5:
                        opponent_tomiddle = sensing_info.opponent_cars_info[0]['to_middle']
                        if abs(to_be_target[0] - opponent_tomiddle) < abs(to_be_target[0] - to_middle):
                            target = to_be_target[1]
                            target_selected = True
                        else:
                            target = to_be_target[0]
                            target_selected = True

                if not target_selected:
                    if abs(to_be_target[0] - to_middle) < abs(to_be_target[1] - to_middle):
                        target = to_be_target[0]
                        target_selected = True
                    else:
                        target = to_be_target[1]
                        target_selected = True

        elif len(sensing_info.track_forward_obstacles) > 2 and (
                (sensing_info.track_forward_obstacles[2]['dist'] - obs_dist) < 40 or
                sensing_info.track_forward_obstacles[2]['dist'] < 60):
            third_obs_tomiddle = sensing_info.track_forward_obstacles[2]['to_middle']
            if abs(third_obs_tomiddle - sensing_info.to_middle) < 4:
                # print("obstacles > 1 and obs_dist < 30")
                to_be_target = [third_obs_tomiddle - 5, third_obs_tomiddle + 5]

                for i in range(2):
                    if abs(to_be_target[i]) > (self.half_road_limit - 1.25):
                        target = to_be_target[1 - i]
                        target_selected = True
                        break
                    if (to_be_target[i] - third_obs_tomiddle) * (
                            sensing_info.track_forward_obstacles[0]['to_middle'] - third_obs_tomiddle) > 0:
                        if abs((to_be_target[i] - third_obs_tomiddle)) > abs(
                                sensing_info.track_forward_obstacles[0]['to_middle'] - third_obs_tomiddle):
                            target = to_be_target[1 - i]
                            target_selected = True
                            break

                if not target_selected:
                    if len(sensing_info.opponent_cars_info) > 0 and abs(sensing_info.opponent_cars_info[0]['dist']) < 5:
                        opponent_tomiddle = sensing_info.opponent_cars_info[0]['to_middle']
                        if abs(to_be_target[0] - opponent_tomiddle) < abs(to_be_target[0] - to_middle):
                            target = to_be_target[1]
                            target_selected = True
                        else:
                            target = to_be_target[0]
                            target_selected = True
                if not target_selected:
                    if abs(to_be_target[0] - to_middle) < abs(to_be_target[1] - to_middle):
                        target = to_be_target[0]
                        target_selected = True
                    else:
                        target = to_be_target[1]
                        target_selected = True

        if obs_dist < 40 and abs(obs_to_mid - to_middle) < 3.0 and obs_to_mid != -2.51 and obs_to_mid != -4.37 and obs_to_mid != 6.07 and obs_to_mid != 3.7:

            if abs(obs_to_mid - to_middle) < 2.5 and sensing_info.speed > 70:
                # print("2---")
                self.set_throttle = 0.0

            car_obs_angle = 0
            if obs_dist > 0:
                car_obs_angle = math.atan(abs(diff) / obs_dist) * 180 / math.pi
            if diff < 0:
                car_obs_angle *= -1.0

            forward_angle_cnt = sensing_info.track_forward_obstacles[0]['dist']
            forward_angle_cnt /= 10.0
            forward_angle_cnt = int(forward_angle_cnt)
            obs_foward_angle = 0.0
            if forward_angle_cnt > 0:
                obs_foward_angle = np.std(sensing_info.track_forward_angles[0:forward_angle_cnt])
            else:
                obs_foward_angle = sensing_info.track_forward_angles[0]

            car_obs_angle -= sensing_info.moving_angle

            if obs_dist < 10.0:
                if abs(car_obs_angle) < 30.0 and obs_foward_angle < 1.1:
                    if diff < 0:
                        target = -20.0
                    else:
                        target = 20.0
            else:
                if abs(car_obs_angle) < 10.0 and obs_foward_angle < 1.1:
                    target *= 1.6
                    if target > 13.0:
                        target = 13.0
                    elif target < -13.0:
                        target = -13.0

            if (obs_to_mid == 2.99 or obs_to_mid == -2.3) and abs(to_middle) < 4:
                target *= 1.2

        elif sensing_info.speed > 120:
            target *= 0.7			

        if target_selected:
            self.steering_by_middle = round(self.steer_val_by_to_middle(to_middle - target), 4)
            self.steering_by_angle = round(self.steer_by_forward_road(sensing_info), 4)

    def steer_by_forward_road(self, sensing_info):
        return (sensing_info.track_forward_angles[0] - sensing_info.moving_angle) / 60

    def steer_val_by_to_middle(self, to_middle):
        steering = abs(to_middle) / 50
        if to_middle > 0:
            steering *= -1
        return steering


if __name__ == '__main__':
    client = DrivingClient()
    client.run()
