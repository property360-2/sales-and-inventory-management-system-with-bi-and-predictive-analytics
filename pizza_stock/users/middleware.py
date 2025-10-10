from django.utils.deprecation import MiddlewareMixin

class BranchContextMiddleware(MiddlewareMixin):
    """Add current branch to request context"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Get selected branch from session or user's first branch
            branch_id = request.session.get('current_branch_id')
            
            if branch_id:
                from inventory.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                    if request.user.can_access_branch(branch):
                        request.current_branch = branch
                    else:
                        request.current_branch = request.user.branches.first()
                except Branch.DoesNotExist:
                    request.current_branch = request.user.branches.first()
            else:
                request.current_branch = request.user.branches.first()
            
            # Save to session
            if request.current_branch:
                request.session['current_branch_id'] = request.current_branch.id
        else:
            request.current_branch = None