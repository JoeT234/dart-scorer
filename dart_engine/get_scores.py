"""
Scoring logic adapted from dart-sense by bnww.
Maps normalized (0-1) boardplane coordinates to dart scores.
"""
import numpy as np
import cv2


class GetScores:
    def __init__(self):
        ring = 10.0
        bullseye_wire = 1.6

        self.scoring_names = np.array(['DB', 'SB', 'S', 'T', 'S', 'D', 'miss'])
        self.scoring_radii = np.array([0, 6.35, 15.9, 107.4 - ring, 107.4, 170.0 - ring, 170.0])
        self.scoring_radii[1:3] += (bullseye_wire / 2)
        self.scoring_radii /= 451.0  # normalize to 0-1

        self.segment_angles = np.array([-9, 9, 27, 45, 63, -81, -63, -45, -27])
        self.segment_numbers = np.array(([6, 11], [10, 14], [15, 9], [2, 12], [17, 5],
                                         [19, 1], [7, 18], [16, 4], [8, 13]))

        # boardplane calibration coords for segments 20, 3, 11, 6 (+ 9, 15)
        self.boardplane_calibration_coords = -np.ones((6, 2))
        h = self.scoring_radii[-1]

        a = h * np.cos(np.deg2rad(81))
        o = (h ** 2 - a ** 2) ** 0.5
        self.boardplane_calibration_coords[0] = [0.5 - a, 0.5 - o]
        self.boardplane_calibration_coords[1] = [0.5 + a, 0.5 + o]

        a = h * np.cos(np.deg2rad(-9))
        o = (h ** 2 - a ** 2) ** 0.5
        self.boardplane_calibration_coords[2] = [0.5 - a, 0.5 + o]
        self.boardplane_calibration_coords[3] = [0.5 + a, 0.5 - o]

        a = h * np.cos(np.deg2rad(27))
        o = (h ** 2 - a ** 2) ** 0.5
        self.boardplane_calibration_coords[4] = [0.5 - a, 0.5 - o]
        self.boardplane_calibration_coords[5] = [0.5 + a, 0.5 + o]

    def find_homography(self, calibration_coords, image_shape):
        """
        calibration_coords: (6,2) normalized coords, -1 means not set
        image_shape: scalar (square)
        """
        mask = np.all(np.logical_and(calibration_coords >= 0, calibration_coords <= 1), axis=1)
        if mask.sum() < 4:
            return None, None
        H, status = cv2.findHomography(
            calibration_coords[mask] * image_shape,
            self.boardplane_calibration_coords[mask] * image_shape
        )
        return H, status

    def transform_to_boardplane(self, matrix, dart_coords, image_shape):
        if len(dart_coords) == 0:
            return dart_coords
        homogenous = np.concatenate(
            (dart_coords * image_shape, np.ones((dart_coords.shape[0], 1))), axis=1
        ).T
        transformed = matrix @ homogenous
        transformed /= transformed[-1]
        transformed = transformed[:-1].T
        transformed /= image_shape
        return transformed

    def score(self, transformed_darts):
        darts = ['' for _ in range(len(transformed_darts))]
        total = 0
        if len(darts) == 0:
            return darts, total

        td = transformed_darts.copy()
        mask = td[:, 0] == 0.5
        td[mask, 0] += 0.00001

        angles = np.rad2deg(np.arctan((td[:, 1] - 0.5) / (td[:, 0] - 0.5)))
        angles = np.where(angles > 0, np.floor(angles), np.ceil(angles))

        for i in range(len(td)):
            dc = td[i]
            if abs(angles[i]) >= 81:
                possible = np.array([3, 20])
            else:
                idx = np.where(self.segment_angles == max(self.segment_angles[self.segment_angles <= angles[i]]))[0]
                possible = self.segment_numbers[idx][0]

            coord_index = 0 if all(possible == [6, 11]) else 1
            number = possible[0] if dc[coord_index] > 0.5 else possible[1]

            distance = ((dc[0] - 0.5) ** 2 + (dc[1] - 0.5) ** 2) ** 0.5
            region = self.scoring_names[np.argmax(self.scoring_radii[distance > self.scoring_radii])]

            scores = {
                'DB': ('DB', 50), 'SB': ('SB', 25),
                'S': (f'S{number}', number), 'T': (f'T{number}', number * 3),
                'D': (f'D{number}', number * 2), 'miss': ('miss', 0)
            }
            darts[i] = scores[region][0]
            total += scores[region][1]

        return darts, total
