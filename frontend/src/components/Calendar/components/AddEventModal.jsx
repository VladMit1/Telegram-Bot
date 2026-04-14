import { useState } from 'react';
import {
   useGetContactsQuery,
   useAddLessonMutation,
} from '../../../store/apiSlice';

export const AddEventModal = ({ onClose, selectedDate, initialStudent }) => {
   // Загружаем контакты только если ученик не передан заранее
   const { data: contacts = [] } = useGetContactsQuery(undefined, {
      skip: !!initialStudent,
   });

   const [addLesson, { isLoading }] = useAddLessonMutation();

   const [formData, setFormData] = useState({
      student_id: initialStudent?.id || '',
      time: '12:00', // Стандарт HH:mm
      topic: '',
      duration: 60,
   });

   const handleSave = async () => {
      if (!formData.student_id) return alert('Выберите ученика');

      try {
         await addLesson({
            ...formData,
            date: selectedDate.format('YYYY-MM-DD'),
         }).unwrap();

         // Уведомление для Telegram
         window.Telegram?.WebApp?.HapticFeedback.notificationOccurred(
            'success'
         );
         onClose();
      } catch (err) {
         console.error('Ошибка:', err);
      }
   };
   const hours = Array.from({ length: 24 }, (_, i) =>
      i.toString().padStart(2, '0')
   );
   const minutes = [
      '00',
      '05',
      '10',
      '15',
      '20',
      '25',
      '30',
      '35',
      '40',
      '45',
      '50',
      '55',
   ];

   // Внутри компонента AddEventModal:
   const [h, m] = formData.time.split(':');

   const handleTimeChange = (newH, newM) => {
      setFormData({ ...formData, time: `${newH}:${newM}` });
   };
   return (
      <div className="modal-overlay" onClick={onClose}>
         <div className="add-event-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="modal-handle" />

            <header className="sheet-header">
               <h3>Запланировать</h3>
               <span className="date-badge">
                  {selectedDate.format('D MMMM')}
               </span>
            </header>

            <div className="form-body">
               {/* ВЫБОР УЧЕНИКА */}
               <div className="input-group">
                  <label>Ученик</label>
                  {initialStudent ? (
                     <div className="static-student">
                        <div className="avatar">{initialStudent.name[0]}</div>
                        <span>{initialStudent.name}</span>
                     </div>
                  ) : (
                     <select
                        className="modern-select"
                        value={formData.student_id}
                        onChange={(e) =>
                           setFormData({
                              ...formData,
                              student_id: e.target.value,
                           })
                        }
                     >
                        <option value="">Кто будет учиться?</option>
                        {contacts.map((c) => (
                           <option key={c.id} value={c.id}>
                              {c.name}
                           </option>
                        ))}
                     </select>
                  )}
               </div>

               <div className="row">
                  {/* ВРЕМЯ (24ч) */}
                  <div className="input-group">
                     <label>Начало</label>
                     <div className="custom-time-picker">
                        <select
                           value={h}
                           onChange={(e) => handleTimeChange(e.target.value, m)}
                        >
                           {hours.map((hour) => (
                              <option key={hour} value={hour}>
                                 {hour}
                              </option>
                           ))}
                        </select>
                        <span>:</span>
                        <select
                           value={m}
                           onChange={(e) => handleTimeChange(h, e.target.value)}
                        >
                           {minutes.map((min) => (
                              <option key={min} value={min}>
                                 {min}
                              </option>
                           ))}
                        </select>
                     </div>
                  </div>

                  {/* ДЛИТЕЛЬНОСТЬ */}
                  <div className="input-group">
                     <label>Длительность</label>
                     <select
                        value={formData.duration}
                        onChange={(e) =>
                           setFormData({
                              ...formData,
                              duration: Number(e.target.value),
                           })
                        }
                     >
                        <option value={45}>45 мин</option>
                        <option value={60}>60 мин</option>
                        <option value={90}>90 мин</option>
                     </select>
                  </div>
               </div>

               <div className="input-group">
                  <label>Тема занятия</label>
                  <input
                     type="text"
                     placeholder="Напр: Speaking Practice"
                     value={formData.topic}
                     onChange={(e) =>
                        setFormData({ ...formData, topic: e.target.value })
                     }
                  />
               </div>

               <button
                  className="submit-btn"
                  onClick={handleSave}
                  disabled={isLoading || !formData.student_id}
               >
                  {isLoading ? 'Сохранение...' : 'Запланировать урок'}
               </button>
            </div>
         </div>
      </div>
   );
};
