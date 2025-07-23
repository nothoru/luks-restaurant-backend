import numpy as np
import cv2
import base64
from deepface import DeepFace
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import FacialData

User = get_user_model()

# --- Helper Functions ---
def decode_image(base64_string):
    image_data = base64.b64decode(base64_string.split(',')[-1])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def liveness_check(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray, 1.3, 5)
    return len(faces) > 0

# --- Upload face (register/update) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_face(request):
    try:
        img = decode_image(request.data['image'])

        if not liveness_check(img):
            return Response({"error": "Liveness check failed"}, status=400)

        embedding = DeepFace.represent(img_path=img, model_name='Facenet')[0]["embedding"]
        encoding = np.asarray(embedding, dtype=np.float32).tobytes()

        FacialData.objects.update_or_create(user=request.user, defaults={'encoding': encoding})
        return Response({"status": "Face data uploaded successfully"})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# --- Verify face (login) ---
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_face(request):
    try:
        img = decode_image(request.data['image'])

        if not liveness_check(img):
            return Response({"verified": False, "error": "Liveness check failed"}, status=400)

        input_embedding = DeepFace.represent(img_path=img, model_name='Facenet')[0]["embedding"]
        input_encoding = np.asarray(input_embedding, dtype=np.float32)

        for face_data in FacialData.objects.select_related("user").all():
            saved_encoding = np.frombuffer(face_data.encoding, dtype=np.float32)
            distance = np.linalg.norm(saved_encoding - input_encoding)

            if distance < 10:
                user = face_data.user
                if user.role not in ['admin', 'staff']:
                    return Response({"verified": False, "error": "Unauthorized role"}, status=403)

                refresh = RefreshToken.for_user(user)
                return Response({
                    "verified": True,
                    "token": str(refresh.access_token),
                    "user_id": user.id,
                    "role": user.role
                })

        return Response({"verified": False, "error": "Face not recognized."}, status=401)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# --- Delete face ---
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_face(request):
    try:
        FacialData.objects.get(user=request.user).delete()
        return Response({"status": "Face data deleted"})
    except FacialData.DoesNotExist:
        return Response({"status": "No face data to delete"})
