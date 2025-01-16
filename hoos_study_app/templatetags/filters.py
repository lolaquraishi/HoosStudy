#https://www.youtube.com/watch?v=r3AMyG3LjNo

from django import template

register = template.Library()

@register.filter(name='filter_count_study_session')
def filter_count_study_session(availabilities, time_slot):
    # print("the filter is being reached")
    count = 0
    for availability in availabilities:
        # print(availability)
        if availability.time_slots and availability.time_slots != "":
            available_slots = [slot.strip() for slot in availability.time_slots.split(",")]
            if time_slot.strip() in available_slots:
                count += 1
                # print("count plus 1")
        # else:
        #     print("invalid")

    return count

