{% extends 'base.html' %}

{% block title %}Orders Management - Pizza Stock Management{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">
            <i class="fas fa-shopping-cart mr-2"></i>
            Orders Management
        </h1>
        <p class="mt-2 text-sm text-gray-600">
            Manage and track orders for {{ request.current_branch.name }}
        </p>
    </div>

    <!-- Quick Stats -->
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div class="bg-white overflow-hidden shadow-lg rounded-lg card-hover">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="bg-yellow-500 rounded-md p-3">
                            <i class="fas fa-clock text-white text-xl"></i>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Pending Payment</dt>
                            <dd class="text-2xl font-bold text-gray-900">{{ summary.pending }}</dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white overflow-hidden shadow-lg rounded-lg card-hover">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="bg-green-500 rounded-md p-3">
                            <i class="fas fa-check-circle text-white text-xl"></i>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Paid</dt>
                            <dd class="text-2xl font-bold text-gray-900">{{ summary.paid }}</dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white overflow-hidden shadow-lg rounded-lg card-hover">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="bg-blue-500 rounded-md p-3">
                            <i class="fas fa-fire text-white text-xl"></i>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Preparing</dt>
                            <dd class="text-2xl font-bold text-gray-900">{{ summary.preparing }}</dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white overflow-hidden shadow-lg rounded-lg card-hover">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="bg-purple-500 rounded-md p-3">
                            <i class="fas fa-bell text-white text-xl"></i>
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Ready</dt>
                            <dd class="text-2xl font-bold text-gray-900">{{ summary.ready }}</dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Filters -->
    <div class="mb-6">
        <div class="inline-flex rounded-md shadow-sm" role="group">
            <a href="?" class="px-4 py-2 text-sm font-medium {% if not selected_status %}bg-indigo-600 text-white{% else %}bg-white text-gray-700 hover:bg-gray-50{% endif %} border border-gray-200 rounded-l-lg">
                Active Orders
            </a>
            {% for status_code, status_name in status_choices %}
            <a href="?status={{ status_code }}" class="px-4 py-2 text-sm font-medium {% if selected_status == status_code %}bg-indigo-600 text-white{% else %}bg-white text-gray-700 hover:bg-gray-50{% endif %} border-t border-b border-r border-gray-200 {% if forloop.last %}rounded-r-lg{% endif %}">
                {{ status_name }}
            </a>
            {% endfor %}
        </div>
    </div>

    <!-- Orders List -->
    <div class="grid grid-cols-1 gap-6">
        {% for order in page_obj %}
        <div class="bg-white shadow-lg rounded-lg overflow-hidden hover:shadow-xl transition">
            <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <div class="flex items-center mb-2">
                            <h3 class="text-xl font-bold text-gray-900 mr-3">
                                Order #{{ order.order_number }}
                            </h3>
                            <span class="px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full
                                {% if order.status == 'pending' %}bg-yellow-100 text-yellow-800
                                {% elif order.status == 'paid' %}bg-green-100 text-green-800
                                {% elif order.status == 'preparing' %}bg-blue-100 text-blue-800
                                {% elif order.status == 'ready' %}bg-purple-100 text-purple-800
                                {% elif order.status == 'completed' %}bg-gray-100 text-gray-800
                                {% elif order.status == 'cancelled' %}bg-red-100 text-red-800
                                {% endif %}">
                                {{ order.get_status_display }}
                            </span>
                        </div>
                        <div class="flex items-center space-x-4 text-sm text-gray-600">
                            <span><i class="fas fa-clock mr-1"></i>{{ order.created_at|date:"M d, Y H:i" }}</span>
                            {% if order.customer_name %}
                            <span><i class="fas fa-user mr-1"></i>{{ order.customer_name }}</span>
                            {% endif %}
                            {% if order.customer_phone %}
                            <span><i class="fas fa-phone mr-1"></i>{{ order.customer_phone }}</span>
                            {% endif %}
                            {% if order.table_number %}
                            <span><i class="fas fa-chair mr-1"></i>Table {{ order.table_number }}</span>
                            {% endif %}
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-2xl font-bold text-indigo-600">₱{{ order.total_amount }}</p>
                        <p class="text-sm text-gray-500">{{ order.get_payment_method_display }}</p>
                    </div>
                </div>

                <!-- Order Items -->
                <div class="border-t border-gray-200 pt-4 mb-4">
                    <h4 class="text-sm font-semibold text-gray-700 mb-2">Items:</h4>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {% for item in order.items.all %}
                        <div class="flex items-center space-x-2 text-sm">
                            <i class="fas fa-pizza-slice text-orange-500"></i>
                            <span class="text-gray-900">{{ item.sku.name }}</span>
                            <span class="text-gray-500">x{{ item.quantity }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Actions -->
                {% if user.is_manager %}
                <div class="flex items-center space-x-2">
                    {% if order.status == 'pending' %}
                    <button onclick="updateStatus({{ order.id }}, 'paid')" 
                            class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium">
                        <i class="fas fa-check mr-1"></i> Mark as Paid
                    </button>
                    {% endif %}
                    
                    {% if order.status == 'paid' %}
                    <button onclick="updateStatus({{ order.id }}, 'preparing')" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium">
                        <i class="fas fa-fire mr-1"></i> Start Preparing
                    </button>
                    {% endif %}
                    
                    {% if order.status == 'preparing' %}
                    <button onclick="updateStatus({{ order.id }}, 'ready')" 
                            class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-sm font-medium">
                        <i class="fas fa-bell mr-1"></i> Mark as Ready
                    </button>
                    {% endif %}
                    
                    {% if order.status == 'ready' %}
                    <button onclick="updateStatus({{ order.id }}, 'completed')" 
                            class="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition text-sm font-medium">
                        <i class="fas fa-check-circle mr-1"></i> Complete Order
                    </button>
                    {% endif %}
                    
                    <a href="{% url 'orders:detail' order.id %}" 
                       class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition text-sm font-medium">
                        <i class="fas fa-eye mr-1"></i> View Details
                    </a>
                    
                    {% if order.can_cancel %}
                    <a href="{% url 'orders:cancel' order.id %}" 
                       class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium">
                        <i class="fas fa-times mr-1"></i> Cancel
                    </a>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>
        {% empty %}
        <div class="bg-white shadow-lg rounded-lg p-12 text-center">
            <i class="fas fa-shopping-cart text-gray-300 text-6xl mb-4"></i>
            <h3 class="text-xl font-bold text-gray-900 mb-2">No orders found</h3>
            <p class="text-gray-600">Orders will appear here as customers place them</p>
        </div>
        {% endfor %}
    </div>

    <!-- Pagination -->
    {% if page_obj.has_other_pages %}
    <div class="mt-8 flex justify-center">
        <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
            {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}{% if selected_status %}&status={{ selected_status }}{% endif %}" 
               class="relative inline-flex items-center px-4 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                Previous
            </a>
            {% endif %}
            
            <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}
            </span>
            
            {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}{% if selected_status %}&status={{ selected_status }}{% endif %}" 
               class="relative inline-flex items-center px-4 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50">
                Next
            </a>
            {% endif %}
        </nav>
    </div>
    {% endif %}
</div>

<script>
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function updateStatus(orderId, newStatus) {
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/orders/${orderId}/update-status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to update order status');
    });
}
</script>
{% endblock %}