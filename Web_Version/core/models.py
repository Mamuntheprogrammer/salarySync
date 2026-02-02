from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class BaseModel(models.Model):
    """
    Abstract base model to track creation and updates.
    Includes:
    - created_at: timestamp when record was created
    - created_by: user who created the record
    - updated_at: timestamp when record was last updated
    - updated_by: user who last updated the record
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="The date and time when this record was created."
    )
    created_by = models.ForeignKey(
        User,
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user who created this record."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when this record was last updated."
    )
    updated_by = models.ForeignKey(
        User,
        related_name="%(class)s_updated",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user who last updated this record."
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']  # optional: default ordering
        verbose_name = "Base Model"
        verbose_name_plural = "Base Models"

    def save(self, *args, **kwargs):
        """
        Optional: override save to set created_by / updated_by automatically
        if you implement a middleware that stores current user in thread-local.
        """
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__} ({self.pk})"
