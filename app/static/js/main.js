// Shared front-end JavaScript.

/**
 * Wires up three <select> elements (course -> semester -> section) so
 * that choosing a course repopulates the semester list with only that
 * course's semesters, and choosing a semester repopulates the section
 * list the same way. Also used later for the attendance page's
 * Course -> Semester -> Section -> Subject chain.
 *
 * options.data shape:
 *   [{ id, name, semesters: [{ id, number, sections: [{ id, name }] }] }]
 */
function initCascadingDropdowns(options) {
    const {
        data,
        courseSelectId,
        semesterSelectId,
        sectionSelectId,
        selectedCourseId,
        selectedSemesterId,
        selectedSectionId,
    } = options;

    const courseSelect = document.getElementById(courseSelectId);
    const semesterSelect = document.getElementById(semesterSelectId);
    const sectionSelect = document.getElementById(sectionSelectId);
    if (!courseSelect || !semesterSelect || !sectionSelect) return;

    function fillSelect(select, items, valueKey, labelFn, placeholder, selectedValue) {
        select.innerHTML = "";
        const blank = document.createElement("option");
        blank.value = "";
        blank.textContent = placeholder;
        select.appendChild(blank);

        items.forEach((item) => {
            const opt = document.createElement("option");
            opt.value = item[valueKey];
            opt.textContent = labelFn(item);
            if (selectedValue && String(item[valueKey]) === String(selectedValue)) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });
    }

    function findCourse(id) {
        return data.find((c) => String(c.id) === String(id));
    }

    function findSemester(course, id) {
        return course ? course.semesters.find((s) => String(s.id) === String(id)) : null;
    }

    function populateSemesters(courseId, keepSemesterId, keepSectionId) {
        const course = findCourse(courseId);
        const semesters = course ? course.semesters : [];
        fillSelect(semesterSelect, semesters, "id", (s) => `Semester ${s.number}`,
            "Select semester", keepSemesterId);
        populateSections(courseId, semesterSelect.value, keepSectionId);
    }

    function populateSections(courseId, semesterId, keepSectionId) {
        const course = findCourse(courseId);
        const semester = findSemester(course, semesterId);
        const sections = semester ? semester.sections : [];
        fillSelect(sectionSelect, sections, "id", (s) => `Section ${s.name}`,
            "Select section", keepSectionId);
    }

    // Initial population, keeping the current value selected (for edit forms).
    fillSelect(courseSelect, data, "id", (c) => c.name, "Select course", selectedCourseId);
    populateSemesters(courseSelect.value, selectedSemesterId, selectedSectionId);

    courseSelect.addEventListener("change", () => populateSemesters(courseSelect.value));
    semesterSelect.addEventListener("change", () =>
        populateSections(courseSelect.value, semesterSelect.value)
    );
}
