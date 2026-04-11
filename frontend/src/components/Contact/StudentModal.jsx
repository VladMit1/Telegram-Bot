import { motion } from 'framer-motion';
import { X, Play, BarChart, GraduationCap } from 'lucide-react';
import moment from 'moment';
export const StudentModal = ({ student, onClose }) => {
   // 1. Настройки времени
   const startOfMonth = moment().startOf('month');
   const daysInMonth = moment().daysInMonth();

   // 2. Вычисляем смещение (0 = Пн, 1 = Вт ... 6 = Вс)
   // isoWeekday() возвращает 1 для Пн. Вычитаем 1, чтобы получить индекс для массива.
   const firstDayOffset = startOfMonth.isoWeekday() - 1;

   // 3. Создаем массив ячеек: сначала пустые для смещения, потом числа месяца
   const calendarCells = [
      ...Array(firstDayOffset).fill(null),
      ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
   ];

   // Заглушка дат (потом заменим на student.attended_days)
   const attendedDays = student.attended_days || [2, 5, 12, 19];
   return (
      <div className="modal-overlay" onClick={onClose}>
         <motion.div
            className="student-modal"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            onClick={(e) => e.stopPropagation()}
         >
            <div className="modal-handle" />

            <header className="modal-header">
               <div className="title">
                  <GraduationCap size={24} />
                  <h2>{student.name}</h2>
               </div>
               <button className="close-btn" onClick={onClose}>
                  <X />
               </button>
            </header>

            <div className="modal-body">
               {/* Мини-календарь активности */}
               <section className="activity-section">
                  <div className="section-header">
                     <h3>{moment().format('MMMM YYYY')}</h3>
                  </div>

                  <div className="calendar-wrapper">
                     {/* Заголовки дней недели */}
                     <div className="weekday-headers">
                        {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((d) => (
                           <span key={d}>{d}</span>
                        ))}
                     </div>

                     {/* Сетка дней */}
                     <div className="month-grid">
                        {calendarCells.map((day, i) => {
                           if (day === null)
                              return (
                                 <div
                                    key={`empty-${i}`}
                                    className="day-cell empty"
                                 />
                              );

                           const isAttended = attendedDays.includes(day);
                           const isToday = day === moment().date();

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

               <div className="progress-card">
                  <div className="book-detail">
                     <span className="label">Текущий материал</span>
                     <h4>{student.last_book || 'Книга не назначена'}</h4>
                     <p>
                        Страница: <strong>{student.last_page || 0}</strong>
                     </p>
                  </div>
                  <button className="btn-primary">
                     <Play size={18} fill="currentColor" />
                     <span>Продолжить урок</span>
                  </button>
               </div>

               <div className="stats-row">
                  <div className="stat-box">
                     <span className="num">{student.total_lessons || 0}</span>
                     <span className="txt">Уроков</span>
                  </div>
                  <div className="stat-box">
                     <span className="num">{student.balance || 0}</span>
                     <span className="txt">Баланс</span>
                  </div>
               </div>
            </div>
         </motion.div>
      </div>
   );
};
