import moment from 'moment';
import { useState } from 'react';

export const StudentCalendar = ({
   attendedDays = [],
   viewDate,
   setViewDate,
}) => {
   const daysInMonth = viewDate.daysInMonth();
   const firstDayWeekday = viewDate.clone().startOf('month').isoWeekday();
   const firstDayOffset = firstDayWeekday - 1;

   const prevMonth = (e) => {
      e.stopPropagation(); // Останавливаем закрытие модалки
      setViewDate(viewDate.clone().subtract(1, 'month'));
   };

   const nextMonth = (e) => {
      e.stopPropagation(); // Останавливаем закрытие модалки
      setViewDate(viewDate.clone().add(1, 'month'));
   };
   const cells = [];
   for (let i = 0; i < firstDayOffset; i++) cells.push(null);
   for (let i = 1; i <= daysInMonth; i++) cells.push(i);
   while (cells.length < 42) cells.push(null);

   return (
      <section className="activity-section">
         <div className="section-header">
            <button className="nav-btn" onClick={prevMonth}>
               &lt;
            </button>
            <h3>{viewDate.format('MMMM YYYY')}</h3>
            <button className="nav-btn" onClick={nextMonth}>
               &gt;
            </button>
         </div>

         <div className="calendar-wrapper">
            <div className="weekday-headers">
               {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d) => (
                  <span key={d}>{d}</span>
               ))}
            </div>
            <div className="month-grid">
               {cells.map((day, i) => {
                  if (day === null)
                     return (
                        <div key={`empty-${i}`} className="day-cell empty" />
                     );

                  // Генерируем строку даты для текущей ячейки
                  const currentFullDate = viewDate
                     .clone()
                     .date(day)
                     .format('YYYY-MM-DD');

                  // Ищем объект урока, который соответствует этой дате
                  const lessonInfo = attendedDays.find(
                     (d) => d.date === currentFullDate
                  );

                  const isToday = moment().isSame(
                     viewDate.clone().date(day),
                     'day'
                  );

                  return (
                     <div
                        key={currentFullDate}
                        className={
                           `day-cell 
                           ${lessonInfo ? 'attended' : ''} 
                           ${isToday ? 'today' : ''} 
                           ${lessonInfo?.status || ''}` // Добавляем класс статуса (planned/completed)
                        }
                        onClick={() =>
                           lessonInfo && alert(`Тема: ${lessonInfo.topic}`)
                        }
                     >
                        <span className="day-number">{day}</span>
                        {lessonInfo && <div className="status-dot" />}
                     </div>
                  );
               })}
            </div>
         </div>
      </section>
   );
};
