"""
Custom password validators
"""

import re
import string
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexPasswordValidator:
    """
    Validate that the password contains:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common patterns
    """
    
    def __init__(self, min_length=12):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        # Check minimum length
        if len(password) < self.min_length:
            raise ValidationError(
                _("This password must contain at least %(min_length)d characters."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("This password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        # Check for digit
        if not re.search(r'\d', password):
            raise ValidationError(
                _("This password must contain at least one digit."),
                code='password_no_digit',
            )
        
        # Check for special character
        special_chars = string.punctuation
        if not any(char in special_chars for char in password):
            raise ValidationError(
                _("This password must contain at least one special character."),
                code='password_no_special',
            )
        
        # Check for common patterns
        self._check_common_patterns(password, user)
    
    def _check_common_patterns(self, password, user):
        """Check for common password patterns"""
        password_lower = password.lower()
        
        # Check for keyboard patterns
        keyboard_patterns = [
            'qwerty', 'asdf', 'zxcv', '1234', 'abcd',
            'qwertyuiop', 'asdfghjkl', 'zxcvbnm',
            '123456789', 'abcdefgh'
        ]
        
        for pattern in keyboard_patterns:
            if pattern in password_lower:
                raise ValidationError(
                    _("This password contains a common keyboard pattern."),
                    code='password_common_pattern',
                )
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            raise ValidationError(
                _("This password contains too many repeated characters."),
                code='password_repeated_chars',
            )
        
        # Check for user-related information
        if user:
            user_info = [
                user.username.lower() if hasattr(user, 'username') else '',
                user.first_name.lower() if hasattr(user, 'first_name') else '',
                user.last_name.lower() if hasattr(user, 'last_name') else '',
                user.email.split('@')[0].lower() if hasattr(user, 'email') else '',
            ]
            
            for info in user_info:
                if info and len(info) > 3 and info in password_lower:
                    raise ValidationError(
                        _("This password is too similar to your personal information."),
                        code='password_too_similar',
                    )
        
        # Check for common substitutions
        common_substitutions = {
            'a': ['@', '4'],
            'e': ['3'],
            'i': ['1', '!'],
            'o': ['0'],
            's': ['$', '5'],
            't': ['7'],
        }
        
        # Reverse common substitutions to check original patterns
        reversed_password = password_lower
        for letter, subs in common_substitutions.items():
            for sub in subs:
                reversed_password = reversed_password.replace(sub, letter)
        
        # Check if reversed password is a common word
        common_words = [
            'password', 'welcome', 'admin', 'login', 'user',
            'resee', 'review', 'study', 'learn', 'content'
        ]
        
        for word in common_words:
            if word in reversed_password:
                raise ValidationError(
                    _("This password is based on a common word."),
                    code='password_common_word',
                )
    
    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters, "
            "including uppercase and lowercase letters, digits, and special characters."
        ) % {'min_length': self.min_length}