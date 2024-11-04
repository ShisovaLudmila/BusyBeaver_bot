from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import types
from state_list import employee
from all_kb import job_title_kb, create_role_kb, hours_kb, year_of_exp_kb, confirm_kb, first_question_kb, questions_kb, main_kb\

router = Router()
       
#хендлер для кнопки соискатель
@router.message(F.text == "соискатель")
async def employee_selection(message : Message, state: FSMContext):
    await message.answer("Для того, чтобы продолжить пользоваться сервисом, заполните данную анкету, строго отвечайте на заданные вопросы")
    await state.set_state(employee.name)
    await message.answer("Введите имя:", reply_markup=first_question_kb)
    
@router.message(employee.confirm, F.text == "начать сначала")
async def start_over_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(employee.name)
    await message.answer("Введите имя:", reply_markup=first_question_kb)
    
@router.message(employee.name)
async def name_selection(message : Message, state : FSMContext):
    await state.update_data(name=message.text)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    await state.set_state(employee.surname)
    await message.answer("Введите фамилию:", reply_markup=questions_kb)

@router.message(employee.surname)
async def surname_selection(message : types.Message, state : FSMContext): 
    await state.update_data(surname=message.text)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    await state.set_state(employee.birthdate)
    await message.answer("Введите дату рождения:", reply_markup=questions_kb)
        
@router.message(employee.birthdate)
async def birthdate_selection(message : types.Message, state : FSMContext):
    await state.update_data(birthdate=message.text)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    await state.set_state(employee.city)
    await message.answer("Введите город проживания:", reply_markup=questions_kb)

@router.message(employee.city)
async def city_selection(message : types.Message, state : FSMContext):
    await state.update_data(city=message.text)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    await state.set_state(employee.time_zone)
    await message.answer("Введите часовой пояс:", reply_markup=questions_kb)
    
@router.message(employee.time_zone)
async def time_zone_selection(message : types.Message, state : FSMContext):
    await state.update_data(time_zone=message.text)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    await state.set_state(employee.job_title)
    await message.answer("Выберете должность из предложенных вариантов:", reply_markup=job_title_kb)
      
@router.callback_query(F.data == 'фулл-тайм', employee.job_title)
async def job_title_selection_full_time(call: types.CallbackQuery, state :FSMContext):
    await state.update_data(job_title=call.data)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(call.message, state)
    #     await call.answer()
    # else:
    await state.set_state(employee.role)
    data = await state.get_data()
    role_kb = data['role'] if 'role' in data else []
    await call.message.answer("Выберите желаемую роль:", reply_markup=create_role_kb(role_kb))
    await call.answer()
        
@router.callback_query(F.data == 'парт-тайм', employee.job_title)
async def job_title_selection_part_time(call: types.CallbackQuery, state :FSMContext):
    await state.update_data(job_title=call.data)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await call.message.answer("Сколько часов в день вы готовы работать:", reply_markup=hours_kb)
    #     await state.set_state(employee.hours)
    #     await call.answer()
    # else:
    await state.set_state(employee.hours)
    await call.message.answer("Сколько часов в день вы готовы работать:", reply_markup=hours_kb)
    await call.answer()
        
@router.callback_query(F.data == 'оба варианта', employee.job_title)
async def job_title_selection_both(call: types.CallbackQuery, state :FSMContext):
    await state.update_data(job_title=call.data)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(call.message, state)
    #     await call.answer()
    # else:
    await state.set_state(employee.hours)
    await call.message.answer("Сколько часов в день вы готовы работать:",reply_markup= hours_kb)
    await call.answer()
    
@router.callback_query(F.data.in_(['1','2','3', '4', '5', '6', '7']), employee.hours)
async def hours_selection(call : types.CallbackQuery, state : FSMContext):
    await state.update_data(hours=call.data)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(call.message, state)
    #     await call.answer()
    # else:
    data = await state.get_data()
    role_kb = data['role'] if 'role' in data else []
    await call.message.answer("Выберите желаемую роль:", reply_markup=create_role_kb(role_kb))
    await state.set_state(employee.role)
    await call.answer()

@router.callback_query(F.data.in_(['менеджер', 'личный ассистент', 'менеджер по закупкам', 'role_done']), employee.role)
async def role_selection(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role_data = data.get("role", [])
    
    if call.data != 'role_done':
        if call.data in role_data:
            role_data.remove(call.data)
        else:
            role_data.append(call.data)

        await state.update_data(role=role_data)
        new_kb = create_role_kb(role_data)

        old_kb = call.message.reply_markup.inline_keyboard
        new_kb_list = new_kb.inline_keyboard
        if old_kb != new_kb_list:
            await call.message.edit_reply_markup(reply_markup=new_kb)
    else:
        # data = await state.get_data()
        # reject = data.get("reject", False)
        # if reject:
        #     await update_on_reject(call.message, state)
        #     call.answer()
        # else:
        await call.message.answer("Сколько у вас лет опыта", reply_markup=year_of_exp_kb)
        await state.set_state(employee.year_of_exp)
        await call.answer()

@router.callback_query(lambda call: call.data in ['0-1','1-3', '3-5', '5-7', '7-10', 'больше 10'], employee.year_of_exp)
async def year_of_exp_selection(call : types.CallbackQuery, state : FSMContext):
    await state.update_data(year_of_exp=call.data)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(call.message, state)
    #     await call.answer()
    # else:
    await call.message.answer("Отправьте свое резюме", reply_markup=questions_kb)
    await state.set_state(employee.resume)
    await call.answer()

@router.message(employee.resume)
async def resume(message : types.Message, state : FSMContext):
    await state.update_data(resume=message.text)
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    await message.answer("Отправте свою видео визитку", reply_markup=questions_kb)
    await state.set_state(employee.video)

@router.message(employee.video)
async def video(message : types.Message, state : FSMContext):
    await state.update_data(video=message.text)
    # await update_on_reject(message, state)
    await update_on_reject(message, state)
    
@router.message( F.text=="подтвердить", employee.confirm)
async def confirm_handler(message : types.Message, state : FSMContext):
    await message.answer("Спасибо за вашу форму!", reply_markup=main_kb)
    await state.clear()
        
async def update_on_reject(message: Message, state: FSMContext): 
    await state.set_state(employee.confirm)
    data = await state.get_data()
    hours_info = f"*Количество часов*: {data['hours']}\n" if 'hours' in data else ""
    roles = ", ".join(data['role']) if isinstance(data['role'], list) else data['role']
    await message.answer(
        (
            f"Ваш данные указанные выше:\n"
            f"*Имя*: {data['name']}\n"
            f"*Фамилия*: {data['surname']}\n"
            f"*Дата рождения*: {data['birthdate']}\n"
            f"*Город*: {data['city']}\n"
            f"*Часовой пояс*: {data['time_zone']}\n"
            f"*Должность*: {data['job_title']}\n"
            f"{hours_info}"
            f"*Роль*: {roles}\n"
            f"*Кол-во лет опыта*: {data['year_of_exp']}\n"
            f"*Резюме*: {data['resume']}\n"
            f"*Видеовизитка*: {data['video']}\n"
        ),
        parse_mode="Markdown",
        reply_markup=confirm_kb
    )

    

# @router.message(employee.confirm, F.text == "утвердить")
# async def process_confirm(message: Message, state: FSMContext) -> None:
#     await state.clear()
#     await message.answer(
#         "Спасибо за вашу форму!",
#         reply_markup=ReplyKeyboardRemove(),
#     ) 
# @router.message(employee.confirm, F.text == "отклонить") 
# async def process_dont_confirm(message: Message, state: FSMContext) -> None:
#     data = await state.get_data()
#     await state.set_state(employee.confirm_reject) 
#     await message.answer( "Какие данные неверны?", reply_markup=change_data_kb_1 if 'hours' in data else change_data_kb_2) 

# @router.message(employee.confirm_reject, F.text != "cancel")
# async def process_reject(message: Message, state: FSMContext) -> None:
#     required_state_index = next(
#         (i for i, obj in enumerate(STATE_LIST) if obj.state_corresponding_button == message.text),
#         None,
#     )
#     if required_state_index is None:
#         await message.answer("Выберете другой пункт")
#     else:
#         required_state = STATE_LIST[required_state_index]
#         await state.update_data(reject=True)
#         print(required_state.state_name)
#         await state.set_state(required_state.state_name)
#         keyboard = required_state.keyboard
#         if(callable(required_state.keyboard)):
#             data = await state.get_data()
#             role_data = data.get("role", [])
#             keyboard = required_state.keyboard(role_data)        
#         await message.answer(
#             required_state.state_question,
#             reply_markup=keyboard
#         )
        
# async def update_on_reject(message: Message, state: FSMContext) -> str: 
#     await state.set_state(employee.confirm) 
#     data = await state.get_data()
#     hours_info = f"Количество часов:{data['hours']}\n" if 'hours' in data else ""
#     roles = ", ".join(data['role']) if isinstance(data['role'], list) else data['role']
#     await message.answer(
#         (
#             f"Пожалуйста, подтвердите ваше данные:\n" 
#             f"Имя:{data['name']}\n"
#             f"Фамилия:{data['surname']}\n"
#             f"Дата рождения:{data['birthdate']}\n"
#             f"Город:{data['city']}\n"
#             f"Часовой пояс:{data['time_zone']}\n"
#             f"Должность:{data['job_title']}\n"
#             f"{hours_info}"
#             f"Роль:{roles}\n"
#             f"Кол-во лет опыта:{data['year_of_exp']}\n"
#             f"резюме:{data['resume']}\n"
#             f"Видеовизитка:{data['video']}\n"
#         ),
#         # reply_markup=confirm_kb
#     )
# await message.answer(f"Все данные:\n{data['name']}\n{data['surname']}\n{data['birthdate']}\n{data['city']}\n{data['time_zone']}\n{data['job_title']}\n{data['hours']}\n{data['role']}\n{data['year_of_exp']}\n{data['resume']}\n{data['video']}")
     
    


    