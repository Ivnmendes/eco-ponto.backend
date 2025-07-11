from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import generics, status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser

from .models import CollectionType, CollectionPoint, PointReview, OperatingHour, PointImage
from .serializers import CollectionPointSerializer, CollectionTypeSerializer, PointReviewSerializer, OperatingHourSerializer, PointImageUploadSerializer, PointImageSerializer, PointStatusUpdateSerializer

def get_all_object_collection_type():
    return CollectionType.objects.all()

def get_all_object_collection_point():
    return CollectionPoint.objects.all().prefetch_related('operating_hours', 'images').select_related('user')

def get_all_object_operating_hour():
    return OperatingHour.objects.all()

def get_all_object_point_review():
    return PointReview.objects.all().select_related('user', 'point')

@extend_schema(tags=["Tipo de coleta"])
class CollectionTypeList(generics.ListCreateAPIView):
    """
    Responsável por lidar com operações para vários tipos de coleta (getAll)
    """
    queryset = get_all_object_collection_type()
    serializer_class = CollectionTypeSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=["Tipo de coleta"])
class CollectionTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Responsável por lidar com operações especificas por tipo de coleta (via id)
    """
    queryset = get_all_object_collection_type()
    serializer_class = CollectionTypeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

@extend_schema(tags=["Ponto de coleta"])
class CollectionPointList(generics.ListCreateAPIView):
    """
    Responsável por lidar com operações para vários pontos de coleta (getAll)
    """
    queryset = get_all_object_collection_point()
    serializer_class = CollectionPointSerializer
    permission_classes = [IsAuthenticated]
    
@extend_schema(tags=["Ponto de coleta"])
class CollectionPointDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Responsável por lidar com operações especificas por ponto de coleta (via id)
    """
    queryset = get_all_object_collection_point()
    serializer_class = CollectionPointSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

@extend_schema(tags=["Horário de funcionamento (ponto de coleta)"])
class OperatingHourList(generics.ListCreateAPIView):
    """
    Lista todos os horários de funcionamento de todos os pontos de coleta ou
    cria um novo horário de funcionamento.
    Ao criar, 'collection_point_id' deve ser fornecido no corpo da requisição.
    """
    queryset = get_all_object_operating_hour()
    serializer_class = OperatingHourSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=["Horário de funcionamento (ponto de coleta)"])
class OperatingHourDetail(generics.ListCreateAPIView):
    """
    Lista todos os horários de funcionamento de um ponto de coleta específico ou
    cria um novo horário de funcionamento para esse ponto de coleta.
    O ID do ponto de coleta é esperado como um parâmetro na URL (ex: /api/collection-points/<collection_point_pk>/operating-hours/).
    """
    serializer_class = OperatingHourSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna uma lista de horários de funcionamento apenas para o ponto de coleta
        especificado no parâmetro 'collection_point_pk' da URL.
        """
        collection_point_pk = self.kwargs.get('collection_point_pk')
        if collection_point_pk is not None:
            return OperatingHour.objects.filter(collection_point_id=collection_point_pk)
        return OperatingHour.objects.none() # Ou levante um erro 404 se o pk não for fornecido e for obrigatório
    
    def perform_create(self, serializer):
        """
        Associa automaticamente o novo horário de funcionamento ao ponto de coleta
        especificado no parâmetro 'collection_point_pk' da URL.
        """
        collection_point_pk = self.kwargs.get('collection_point_pk')
        get_object_or_404(CollectionPoint, pk=collection_point_pk)
        serializer.save(collection_point_id=collection_point_pk)

@extend_schema(tags=["Avaliação do ponto"])
class PointReviewList(generics.ListCreateAPIView):
    """
    Responsável por lidar com operações especificas por review do ponto (getAll)
    """
    queryset = get_all_object_point_review()
    serializer_class = PointReviewSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=["Avaliação do ponto"])
class PointReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Responsável por lidar com operações especificas por review do ponto (via id)
    """
    queryset = get_all_object_point_review()
    serializer_class = PointReviewSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

@extend_schema(
    tags=["Avaliação do ponto"],
    parameters=[
        OpenApiParameter(name="user_id", required=False, description="ID do usuário", type=int),
        OpenApiParameter(name="point_id", required=False, description="ID do ponto de coleta", type=int),
    ]
)
class PointReviewFilteredList(APIView):
    """
    Retorna avaliações filtradas por usuário e/ou ponto de coleta.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        point_id = request.query_params.get('id')

        queryset = PointReview.objects.all()

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if point_id:
            queryset = queryset.filter(collection_point_id=point_id)

        serializer = PointReviewSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Imagem do ponto"],
    request=PointImageUploadSerializer
)
class PointImageUploadView(APIView):
    """
    Responsável por lidar com upload de imagens para pontos de coleta.
    """
    parser_classes = (MultiPartParser,) # Necessário para lidar com uploads de arquivos
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        collection_point = get_object_or_404(CollectionPoint, pk=pk)

        upload_serializer = PointImageUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        image_file = upload_serializer.validated_data['image']
        new_image = PointImage.objects.create(
            collection_point=collection_point,
            image=image_file
        )

        response_serializer = PointImageSerializer(new_image)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
@extend_schema(tags=["Ponto de coleta"])
class UserSubmitedCollectionPointsList(generics.ListAPIView):
    """
    Lista todos os pontos de coleta submetidos pelo usuário logado.
    """
    serializer_class = CollectionPointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna uma lista de pontos de coleta submetidos pelo usuário autenticado.
        """
        user = self.request.user
        return CollectionPoint.objects.filter(user=user).prefetch_related('operating_hours', 'images').select_related('user')

    def get_serializer_context(self):
        """
        Passa o contexto da requisição para o serializer.
        """
        return {'request': self.request}
    
@extend_schema(tags=["Ponto de coleta"])
class ActiveCollectionPointsList(generics.ListAPIView):
    """
    Lista todos os pontos de coleta ativos (is_active=True).
    """
    serializer_class = CollectionPointSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        """
        Retorna uma lista de todos os pontos de coleta ativos.
        """
        return CollectionPoint.objects.filter(is_active=True).prefetch_related('operating_hours', 'images').select_related('user')

    def get_serializer_context(self):
        """
        Passa o contexto da requisição para o serializer.
        """
        return {'request': self.request}

@extend_schema(tags=["Ponto de coleta"])
class InactiveCollectionPointsList(generics.ListAPIView):
    """
    Lista todos os pontos de coleta inativos (is_active=False).
    Esta rota pode ser mais útil para administradores.
    """
    serializer_class = CollectionPointSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna uma lista de todos os pontos de coleta inativos.
        """
        return CollectionPoint.objects.filter(is_active=False, status='pending').prefetch_related('operating_hours', 'images').select_related('user')

    def get_serializer_context(self):
        """
        Passa o contexto da requisição para o serializer.
        """
        return {'request': self.request}

@extend_schema(
    tags=["Ponto de coleta (Admin)"],
    request=PointStatusUpdateSerializer,
    responses={200: CollectionPointSerializer}
)
class UpdatePointStatusView(generics.UpdateAPIView):
    """
    Endpoint para administradores aprovarem ou rejeitarem um ponto de coleta.
    Atualiza os campos 'is_active' e 'status'.
    """
    queryset = get_all_object_collection_point()
    serializer_class = PointStatusUpdateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'