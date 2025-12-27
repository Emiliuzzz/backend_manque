from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from inmobiliaria.models import Interesado, SolicitudCliente
from inmobiliaria.serializers import InteresadoSerializer, SolicitudClienteSerializer


class MiPerfilClienteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        interesado = Interesado.objects.filter(usuario=user).first()
        if not interesado:
            return Response(
                {"detail": "No se encontró un perfil de cliente asociado a tu cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = InteresadoSerializer(interesado).data
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        interesado = Interesado.objects.filter(usuario=user).first()
        if not interesado:
            return Response(
                {"detail": "No se encontró un perfil de cliente asociado a tu cuenta."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InteresadoSerializer(interesado, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MisSolicitudesClienteView(generics.ListAPIView):
    serializer_class = SolicitudClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            SolicitudCliente.objects
            .select_related("interesado")
            .filter(interesado__usuario=user)
            .order_by("-created_at")
        )