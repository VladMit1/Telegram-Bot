import moment from 'moment';
import { useState } from 'react';

export const StudentCalendar = ({ attendedDays }) => {
   const [viewDate, setViewDate] = useState(moment());

   const daysInMonth = viewDate.daysInMonth();
   const firstDayWeekday = viewDate.clone().startOf('month').isoWeekday();
   const firstDayOffset = firstDayWeekday - 1;

   const calendarCells = [
      ...Array(firstDayOffset).fill(null),
      ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
   ];

   const finalCalendarCells = [
      ...calendarCells,
      ...Array(42 - calendarCells.length).fill(null),
   ];

   const prevMonth = () => setViewDate(viewDate.clone().subtract(1, 'month'));
   const nextMonth = () => setViewDate(viewDate.clone().add(1, 'month'));

   return (
      <section className="activity-section">
         <div className="section-header">
            <button onClick={prevMonth}>&lt;</button>
            <h3>{viewDate.format('MMMM YYYY')}</h3>
            <button onClick={nextMonth}>&gt;</button>
         </div>

         <div className="calendar-wrapper">
            <div className="weekday-headers">
               {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d) => (
                  <span key={d}>{d}</span>
               ))}
            </div>
            <div className="month-grid">
               {finalCalendarCells.map((day, i) => {
                  if (day === null)
                     return (
                        <div key={`empty-${i}`} className="day-cell empty" />
                     );

                  const isAttended = attendedDays.includes(day);
                  const isToday =
                     viewDate.isSame(moment(), 'month') &&
                     viewDate.isSame(moment(), 'year') &&
                     day === moment().date();

                  return (
                     <div
                        key={day}
                        className={`day-cell ${isAttended ? 'attended' : ''} ${isToday ? 'today' : ''}`}
                     >
                        {day}
                     </div>
                  );
               })}
            </div>
         </div>
      </section>
   );
};
