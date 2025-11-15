from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.authorization.permissions import HasResourcePermission


class MockProductViewSet(viewsets.ViewSet):
    """Mock ViewSet для продуктов с проверкой прав доступа."""
    
    permission_classes = [permissions.IsAuthenticated]
    resource_name = 'products'
    
    # Mock data
    MOCK_PRODUCTS = [
        {'id': 1, 'name': 'Продукт 1', 'price': 100, 'description': 'Описание 1'},
        {'id': 2, 'name': 'Продукт 2', 'price': 200, 'description': 'Описание 2'},
        {'id': 3, 'name': 'Продукт 3', 'price': 300, 'description': 'Описание 3'},
    ]
    
    def get_permissions(self):
        """Возвращает соответствующие классы разрешений на основе действия."""
        if self.action == 'list':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='products', action='list')]
        elif self.action == 'retrieve':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='products', action='read')]
        elif self.action == 'create':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='products', action='create')]
        elif self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='products', action='update')]
        elif self.action == 'destroy':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='products', action='delete')]
        return [permissions.IsAuthenticated()]
    
    def list(self, request):
        """Список всех продуктов."""
        return Response(self.MOCK_PRODUCTS)
    
    def retrieve(self, request, pk=None):
        """Получить конкретный продукт."""
        try:
            product_id = int(pk)
            product = next((p for p in self.MOCK_PRODUCTS if p['id'] == product_id), None)
            if product:
                return Response(product)
            return Response(
                {'error': 'Продукт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Неверный ID продукта'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def create(self, request):
        """Создать новый продукт."""
        data = request.data
        new_id = max([p['id'] for p in self.MOCK_PRODUCTS]) + 1
        product = {
            'id': new_id,
            'name': data.get('name', ''),
            'price': data.get('price', 0),
            'description': data.get('description', '')
        }
        self.MOCK_PRODUCTS.append(product)
        return Response(product, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Обновить продукт."""
        try:
            product_id = int(pk)
            product = next((p for p in self.MOCK_PRODUCTS if p['id'] == product_id), None)
            if not product:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            product.update(request.data)
            return Response(product)
        except ValueError:
            return Response(
                {'error': 'Invalid product ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, pk=None):
        """Частично обновить продукт."""
        return self.update(request, pk)
    
    def destroy(self, request, pk=None):
        """Удалить продукт."""
        try:
            product_id = int(pk)
            product = next((p for p in self.MOCK_PRODUCTS if p['id'] == product_id), None)
            if not product:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            self.MOCK_PRODUCTS.remove(product)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {'error': 'Invalid product ID'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MockOrderViewSet(viewsets.ViewSet):
    """Mock ViewSet для заказов с проверкой прав доступа."""
    
    permission_classes = [permissions.IsAuthenticated]
    resource_name = 'orders'
    
    # Mock data
    MOCK_ORDERS = [
        {'id': 1, 'user_id': 1, 'product_ids': [1, 2], 'total': 300, 'status': 'pending'},
        {'id': 2, 'user_id': 2, 'product_ids': [2, 3], 'total': 500, 'status': 'completed'},
        {'id': 3, 'user_id': 1, 'product_ids': [1], 'total': 100, 'status': 'pending'},
    ]
    
    def get_permissions(self):
        """Возвращает соответствующие классы разрешений на основе действия."""
        if self.action == 'list':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='orders', action='list')]
        elif self.action == 'retrieve':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='orders', action='read')]
        elif self.action == 'create':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='orders', action='create')]
        elif self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='orders', action='update')]
        elif self.action == 'destroy':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='orders', action='delete')]
        return [permissions.IsAuthenticated()]
    
    def list(self, request):
        """Список всех заказов."""
        return Response(self.MOCK_ORDERS)
    
    def retrieve(self, request, pk=None):
        """Получить конкретный заказ."""
        try:
            order_id = int(pk)
            order = next((o for o in self.MOCK_ORDERS if o['id'] == order_id), None)
            if order:
                return Response(order)
            return Response(
                {'error': 'Заказ не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Неверный ID заказа'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def create(self, request):
        """Создать новый заказ."""
        data = request.data
        new_id = max([o['id'] for o in self.MOCK_ORDERS]) + 1
        order = {
            'id': new_id,
            'user_id': request.user.id,
            'product_ids': data.get('product_ids', []),
            'total': data.get('total', 0),
            'status': data.get('status', 'pending')
        }
        self.MOCK_ORDERS.append(order)
        return Response(order, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Обновить заказ."""
        try:
            order_id = int(pk)
            order = next((o for o in self.MOCK_ORDERS if o['id'] == order_id), None)
            if not order:
                return Response(
                    {'error': 'Заказ не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            order.update(request.data)
            return Response(order)
        except ValueError:
            return Response(
                {'error': 'Неверный ID заказа'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, pk=None):
        """Частично обновить заказ."""
        return self.update(request, pk)
    
    def destroy(self, request, pk=None):
        """Удалить заказ."""
        try:
            order_id = int(pk)
            order = next((o for o in self.MOCK_ORDERS if o['id'] == order_id), None)
            if not order:
                return Response(
                    {'error': 'Заказ не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            self.MOCK_ORDERS.remove(order)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response(
                {'error': 'Неверный ID заказа'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MockReportViewSet(viewsets.ViewSet):
    """Mock ViewSet для отчетов с проверкой прав доступа."""
    
    permission_classes = [permissions.IsAuthenticated]
    resource_name = 'reports'
    
    # Mock data
    MOCK_REPORTS = [
        {'id': 1, 'name': 'Отчет по продажам', 'type': 'sales', 'period': '2024-01'},
        {'id': 2, 'name': 'Отчет по складу', 'type': 'inventory', 'period': '2024-01'},
    ]
    
    def get_permissions(self):
        """Возвращает соответствующие классы разрешений на основе действия."""
        if self.action == 'list':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='reports', action='list')]
        elif self.action == 'retrieve':
            return [permissions.IsAuthenticated(), HasResourcePermission(resource='reports', action='read')]
        return [permissions.IsAuthenticated()]
    
    def list(self, request):
        """Список всех отчетов."""
        return Response(self.MOCK_REPORTS)
    
    def retrieve(self, request, pk=None):
        """Получить конкретный отчет."""
        try:
            report_id = int(pk)
            report = next((r for r in self.MOCK_REPORTS if r['id'] == report_id), None)
            if report:
                return Response(report)
            return Response(
                {'error': 'Отчет не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {'error': 'Неверный ID отчета'},
                status=status.HTTP_400_BAD_REQUEST
            )

