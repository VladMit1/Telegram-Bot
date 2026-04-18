import moment from 'moment';

export const StudentCalendar = ({
   attendedDays = [],
   viewDate,
   setViewDate,
}) => {
   const daysInMonth = viewDate.daysInMonth();
   const firstDayWeekday = viewDate.clone().startOf('month').isoWeekday();
   const firstDayOffset = firstDayWeekday - 1;

   const cells = [];
   for (let i = 0; i < firstDayOffset; i++) cells.push(null);
   for (let i = 1; i <= daysInMonth; i++) cells.push(i);
   while (cells.length < 42) cells.push(null);

   return (
      <section className="activity-section">
         <div className="section-header">
            <button
               onClick={() =>
                  setViewDate(viewDate.clone().subtract(1, 'month'))
               }
            >
               &lt;
            </button>
            <h3>{viewDate.format('MMMM YYYY')}</h3>
            <button
               onClick={() => setViewDate(viewDate.clone().add(1, 'month'))}
            >
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
                     return <div key={i} className="day-cell empty" />;

                  const dateStr = viewDate
                     .clone()
                     .date(day)
                     .format('YYYY-MM-DD');
                  const dayEvents = attendedDays.filter(
                     (d) => d.date === dateStr
                  );

                  const lesson = dayEvents.find((e) => e.type === 'lesson');
                  const payment = dayEvents.find((e) => e.type === 'payment');
                  const isToday = moment().isSame(
                     viewDate.clone().date(day),
                     'day'
                  );

                  return (
                     <div
                        key={dateStr}
                        className={`day-cell 
                                    ${lesson ? 'attended' : ''} 
                                    ${lesson && !lesson.is_paid ? 'unpaid' : ''} 
                                    ${isToday ? 'today' : ''} 
                                    ${payment ? 'has-payment' : ''}`}
                     >
                        <span className="day-number">{day}</span>
                        <div className="marker">
                           {payment && <div className="coin">🪙</div>}
                        </div>
                     </div>
                  );
               })}
            </div>
         </div>
      </section>
   );
};
