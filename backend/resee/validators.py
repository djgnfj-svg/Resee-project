"""
Custom password and security validators
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


class FileUploadValidator:
    """Validate uploaded files for security"""
    
    def __init__(self, allowed_extensions=None, max_size=None):
        self.allowed_extensions = allowed_extensions or ['.jpg', '.jpeg', '.png', '.gif']
        self.max_size = max_size or 10 * 1024 * 1024  # 10MB
    
    def __call__(self, file):
        import os
        import magic
        
        # Check file size
        if file.size > self.max_size:
            raise ValidationError(
                _("File size exceeds maximum allowed size of %(max_size)s bytes."),
                code='file_too_large',
                params={'max_size': self.max_size}
            )
        
        # Check file extension
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise ValidationError(
                _("File extension '%(extension)s' is not allowed."),
                code='invalid_extension',
                params={'extension': file_ext}
            )
        
        # Check MIME type
        try:
            mime_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # Reset file pointer
            
            allowed_mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            
            expected_mime = allowed_mime_types.get(file_ext)
            if expected_mime and mime_type != expected_mime:
                raise ValidationError(
                    _("File content does not match its extension."),
                    code='mime_mismatch'
                )
                
        except Exception as e:
            raise ValidationError(
                _("Could not validate file content."),
                code='validation_error'
            )
        
        # Check for malicious content
        self._check_malicious_content(file)
    
    def _check_malicious_content(self, file):
        """Check for potentially malicious content in files"""
        # Read file content for scanning
        content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Convert to string for pattern matching (with error handling)
        try:
            content_str = content.decode('utf-8', errors='ignore').lower()
        except:
            content_str = str(content).lower()
        
        # Check for script tags and executable content
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'onclick=',
            b'<?php',
            b'<%',
            b'#!/bin/',
            b'#!/usr/bin/',
        ]
        
        for pattern in malicious_patterns:
            if pattern in content:
                raise ValidationError(
                    _("File contains potentially malicious content."),
                    code='malicious_content'
                )
        
        # Check file headers for common executable signatures
        executable_signatures = [
            b'\x4d\x5a',  # Windows PE
            b'\x7f\x45\x4c\x46',  # Linux ELF
            b'\xfe\xed\xfa',  # macOS Mach-O
            b'\xcf\xfa\xed\xfe',  # macOS Mach-O
        ]
        
        for signature in executable_signatures:
            if content.startswith(signature):
                raise ValidationError(
                    _("Executable files are not allowed."),
                    code='executable_file'
                )


class ContentValidator:
    """Validate user content for security"""
    
    def __init__(self, max_length=None):
        self.max_length = max_length or 100000  # 100KB
    
    def __call__(self, content):
        # Check content length
        if len(content) > self.max_length:
            raise ValidationError(
                _("Content exceeds maximum allowed length."),
                code='content_too_long'
            )
        
        # Check for malicious scripts
        self._check_malicious_scripts(content)
        
        # Check for spam patterns
        self._check_spam_patterns(content)
    
    def _check_malicious_scripts(self, content):
        """Check for malicious script content"""
        content_lower = content.lower()
        
        # Script injection patterns
        script_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<form[^>]*>',
        ]
        
        for pattern in script_patterns:
            if re.search(pattern, content_lower):
                raise ValidationError(
                    _("Content contains potentially malicious scripts."),
                    code='malicious_script'
                )
    
    def _check_spam_patterns(self, content):
        """Check for spam patterns"""
        content_lower = content.lower()
        
        # Common spam indicators
        spam_patterns = [
            r'(viagra|cialis|pharmacy)',
            r'(win\s+money|lottery|prize)',
            r'(click\s+here|visit\s+now)',
            r'(free\s+money|cash\s+now)',
            r'(weight\s+loss|diet\s+pill)',
        ]
        
        spam_count = 0
        for pattern in spam_patterns:
            if re.search(pattern, content_lower):
                spam_count += 1
        
        # If multiple spam patterns found, reject content
        if spam_count >= 2:
            raise ValidationError(
                _("Content appears to be spam."),
                code='spam_content'
            )
        
        # Check for excessive links
        link_count = len(re.findall(r'https?://', content_lower))
        if link_count > 5:
            raise ValidationError(
                _("Content contains too many links."),
                code='excessive_links'
            )
        
        # Check for repeated text
        words = content_lower.split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(words) / len(unique_words)
            
            if repetition_ratio > 3:
                raise ValidationError(
                    _("Content contains too much repeated text."),
                    code='repetitive_content'
                )


class RateLimitValidator:
    """Validate rate limits for user actions"""
    
    def __init__(self, action_type, max_attempts=10, time_window=3600):
        self.action_type = action_type
        self.max_attempts = max_attempts
        self.time_window = time_window
    
    def __call__(self, user, request=None):
        from django.core.cache import cache
        from ipware import get_client_ip
        
        # Use user ID or IP address for rate limiting
        if user and user.is_authenticated:
            identifier = f"user_{user.id}"
        elif request:
            client_ip, _ = get_client_ip(request)
            identifier = f"ip_{client_ip}"
        else:
            identifier = "anonymous"
        
        cache_key = f"rate_limit_{self.action_type}_{identifier}"
        
        # Get current attempt count
        attempts = cache.get(cache_key, 0)
        
        if attempts >= self.max_attempts:
            raise ValidationError(
                _("Too many attempts. Please try again later."),
                code='rate_limit_exceeded'
            )
        
        # Increment attempt count
        cache.set(cache_key, attempts + 1, self.time_window)


class SecurityValidator:
    """General security validation utilities"""
    
    @staticmethod
    def validate_username(username):
        """Validate username for security"""
        # Check length
        if len(username) < 3 or len(username) > 30:
            raise ValidationError(
                _("Username must be between 3 and 30 characters."),
                code='invalid_username_length'
            )
        
        # Check allowed characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(
                _("Username can only contain letters, numbers, underscores, and hyphens."),
                code='invalid_username_chars'
            )
        
        # Check for reserved usernames
        reserved_usernames = [
            'admin', 'root', 'administrator', 'mod', 'moderator',
            'api', 'www', 'mail', 'ftp', 'ssh', 'test', 'demo',
            'support', 'help', 'info', 'contact', 'noreply',
            'resee', 'system', 'user', 'guest', 'anonymous'
        ]
        
        if username.lower() in reserved_usernames:
            raise ValidationError(
                _("This username is reserved and cannot be used."),
                code='reserved_username'
            )
    
    @staticmethod
    def validate_email_domain(email):
        """Validate email domain against blocklist"""
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        # Common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'temp-mail.org', 'throwaway.email'
        ]
        
        if domain in disposable_domains:
            raise ValidationError(
                _("Disposable email addresses are not allowed."),
                code='disposable_email'
            )
    
    @staticmethod
    def validate_content_title(title):
        """Validate content title"""
        if len(title) > 200:
            raise ValidationError(
                _("Title is too long."),
                code='title_too_long'
            )
        
        # Check for malicious patterns
        if re.search(r'<[^>]+>', title):
            raise ValidationError(
                _("Title cannot contain HTML tags."),
                code='html_in_title'
            )
    
    @staticmethod
    def sanitize_input(text, allow_html=False):
        """Sanitize user input"""
        import html
        
        if not allow_html:
            # Escape HTML entities
            text = html.escape(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text