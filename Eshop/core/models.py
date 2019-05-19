from io import BytesIO
import sys
import os

from django.dispatch import receiver
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.dispatch import receiver

from PIL import Image, ImageOps



LABEL_CHOICES = (
    ('NOR', 'Normal'),
    ('NEW', 'New'),
    ('SOL', 'Solde')
)

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.IntegerField()
    discount_price = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING)
    label = models.CharField(choices=LABEL_CHOICES, max_length=3, default='NOR')
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

    # def save(self, *args, **kwargs):
    #     image = Image.open(self.img1)
    #     outputIoStream = BytesIO()
    #     newImage = image.resize((1920, 1280))
    #     newImage.save(outputIoStream, format='JPEG', quality=90)
    #     outputIoStream.seek(0)
    #     self.img1 = InMemoryUploadedFile(outputIoStream,'ImageField', "%s-img1.jpg" %self.title, 'image/jpeg', sys.getsizeof(outputIoStream), None)
    #     super(Item, self).save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=Item)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes img1 from filesystem
    when corresponding `Item` object is deleted.
    """
    if instance.img1:
        if os.path.isfile(instance.img1.path):
            os.remove(instance.img1.path)

@receiver(models.signals.pre_save, sender=Item)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old img1 from filesystem
    when corresponding `Item` object is updated
    with new img1.
    """
    print("pre_save")

    new_file = instance.img1
    print("new_file: " + str(new_file))

    try:
        old_file = Item.objects.get(pk=instance.pk).img1

        if not old_file == new_file:
            print("Same file")
            old_file.close()
            os.remove(old_file.path)
            image = Image.open(new_file)
            outputIoStream = BytesIO()
            newImage = image.resize((1920, 1280))
            newImage.save(outputIoStream, format='JPEG', quality=90)
            outputIoStream.seek(0)
            instance.img1 = InMemoryUploadedFile(outputIoStream,'ImageField', "%s-img1.jpg" %instance.title, 'image/jpeg', sys.getsizeof(outputIoStream), None)

    except Item.DoesNotExist:

        print("New Image")
        image = Image.open(new_file)
        outputIoStream = BytesIO()
        newImage = image.resize((1920, 1280))
        newImage.save(outputIoStream, format='JPEG', quality=90)
        outputIoStream.seek(0)
        instance.img1 = InMemoryUploadedFile(outputIoStream,'ImageField', "%s-img1.jpg" %instance.title, 'image/jpeg', sys.getsizeof(outputIoStream), None)

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
