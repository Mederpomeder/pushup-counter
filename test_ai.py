import cv2
import mediapipe as mp

# Initialize MediaPipe Pose tracking modules
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Open access to your local webcam (0 is usually the default built-in camera)
cap = cv2.VideoCapture(0)

print("AI Model initializing... Press 'q' on your keyboard to exit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frames from webcam.")
        break

    # Convert the frame image color from BGR (OpenCV default) to RGB (MediaPipe requirement)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame with the AI model
    results = pose.process(rgb_frame)

    # If body landmarks are detected, draw them onto the original webcam frame
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )

    # Display the live window
    cv2.imshow('MediaPipe Pose Tracking Test', frame)

    # Break the loop safely if the user presses the 'q' key
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()