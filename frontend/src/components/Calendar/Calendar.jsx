import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import moment from 'moment';
import { ChevronLeft, ChevronRight, Plus, Clock, User } from 'lucide-react';

export const Calendar = () => {
   const [selectedDate, setSelectedDate] = useState(moment());

   // Заглушка событий (в будущем придет из API: /lessons?date=...)
   const events = [
      {
         id: 1,
         time: '10:00',
         duration: '60 мин',
         student: 'Александр Г.',
         topic: 'Present Simple',
      },
      {
         id: 2,
         time: '14:30',
         duration: '45 мин',
         student: 'Мария Л.',
         topic: 'Reading Unit 4',
      },
   ];

   // Генерируем ленту из 7 дней (текущая неделя)
   const weekDays = Array.from({ length: 7 }, (_, i) =>
      moment().startOf('week').add(i, 'days')
   );

   return (
      <div className="event-calendar">
         {/* Селектор даты */}
         <header className="calendar-nav">
            <button
               onClick={() =>
                  setSelectedDate((prev) => prev.clone().subtract(1, 'week'))
               }
            >
               <ChevronLeft size={20} />
            </button>
            <h2>{selectedDate.format('MMMM YYYY')}</h2>
            <button
               onClick={() =>
                  setSelectedDate((prev) => prev.clone().add(1, 'week'))
               }
            >
               <ChevronRight size={20} />
            </button>
         </header>

         {/* Лента дней недели */}
         <div className="days-strip">
            {weekDays.map((day) => {
               const isSelected = day.isSame(selectedDate, 'day');
               return (
                  <div
                     key={day.format()}
                     className={`day-item ${isSelected ? 'active' : ''}`}
                     onClick={() => setSelectedDate(day)}
                  >
                     <span className="weekday">{day.format('dd')}</span>
                     <span className="day-num">{day.date()}</span>
                  </div>
               );
            })}
         </div>

         {/* Список событий на день */}
         <div className="event-list">
            <div className="list-header">
               <span>План на {selectedDate.format('D MMMM')}</span>
               <button className="add-event-btn">
                  <Plus size={18} />
               </button>
            </div>

            <AnimatePresence mode="wait">
               {events.length > 0 ? (
                  events.map((event) => (
                     <motion.div
                        key={event.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="event-card"
                     >
                        <div className="event-time">
                           <Clock size={14} />
                           <span>{event.time}</span>
                           <small>{event.duration}</small>
                        </div>
                        <div className="event-info">
                           <h4>{event.student}</h4>
                           <p>{event.topic}</p>
                        </div>
                        <div className="event-action">
                           <User size={18} />
                        </div>
                     </motion.div>
                  ))
               ) : (
                  <p className="empty-msg">На этот день занятий нет</p>
               )}
            </AnimatePresence>
         </div>
      </div>
   );
};
