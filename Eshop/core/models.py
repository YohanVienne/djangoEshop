from io import BytesIO
import sys

from django.dispatch import receiver
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from django.db import models
from django.shortcuts import reverse

from PIL import Image, ImageOps



LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.IntegerField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    img1 = models.ImageField(upload_to='item/')
    slug = models.SlugField()
    description = models.TextField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })

    def save(self, *args, **kwargs):
        image = Image.open(self.img1)
        outputIoStream = BytesIO()
        newImage = image.resize((1920, 1280))
        newImage.save(outputIoStream, format='JPEG', quality=90)
        outputIoStream.seek(0)
        print(outputIoStream.seek(0))
        self.img1 = InMemoryUploadedFile(outputIoStream,'ImageField', "%s.jpg" %self.img1.name.split('.')[0], 'image/jpeg', sys.getsizeof(outputIoStream), None)
        super(Item, self).save(*args, **kwargs)


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total
