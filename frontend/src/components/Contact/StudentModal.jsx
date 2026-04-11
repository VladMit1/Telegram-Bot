import { motion } from 'framer-motion';
import { X, Play, BarChart, GraduationCap } from 'lucide-react';
import moment from 'moment';
export const StudentModal = ({ student, onClose }) => {
   const daysInMonth = moment().daysInMonth();
   const monthDays = Array.from({ length: daysInMonth }, (_, i) => i + 1);

   // Заглушка: даты занятий. В будущем придут из API как student.attended_days
   const attendedDays = student.attended_days || [2, 5, 8, 12, 15, 19, 22];

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
                  <h3>Активность: {moment().format('MMMM')}</h3>
                  <div className="month-grid">
                     {monthDays.map((day) => (
                        <div
                           key={day}
                           className={`day-cell ${attendedDays.includes(day) ? 'attended' : ''} ${day === moment().date() ? 'today' : ''}`}
                        >
                           {day}
                        </div>
                     ))}
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
