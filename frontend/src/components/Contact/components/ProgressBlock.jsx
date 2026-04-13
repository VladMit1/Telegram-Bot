import { useState } from 'react';
import { Play, Check, X } from 'lucide-react';
import { useUpdateProgressMutation } from '../../../store/apiSlice';

export const ProgressBlock = ({ student }) => {
   const [isEditing, setIsEditing] = useState(false);
   const [book, setBook] = useState(student.last_book || '');
   const [page, setPage] = useState(student.last_page || 0);
   const [updateProgress, { isLoading }] = useUpdateProgressMutation();

   const handleSave = async () => {
      await updateProgress({
         id: student.id,
         last_book: book,
         last_page: Number(page),
      });
      setIsEditing(false);
   };

   return (
      <div className="progress-card">
         <div className="book-detail">
            <span className="label">Текущий материал</span>
            {isEditing ? (
               <div className="edit-box">
                  <input
                     value={book}
                     onChange={(e) => setBook(e.target.value)}
                     placeholder="Книга..."
                  />
                  <input
                     type="number"
                     value={page}
                     onChange={(e) => setPage(e.target.value)}
                     className="page-input"
                  />
                  <div className="edit-btns">
                     <button onClick={handleSave} className="save-btn">
                        <Check size={16} />
                     </button>
                     <button
                        onClick={() => setIsEditing(false)}
                        className="cancel-btn"
                     >
                        <X size={16} />
                     </button>
                  </div>
               </div>
            ) : (
               <div onClick={() => setIsEditing(true)}>
                  <h4>{student.last_book || 'Книга не назначена'}</h4>
                  <p>
                     Страница: <strong>{student.last_page || 0}</strong>
                  </p>
               </div>
            )}
         </div>
         {!isEditing && (
            <button className="btn-primary">
               <Play size={18} fill="currentColor" />
               <span>Урок</span>
            </button>
         )}
      </div>
   );
};
