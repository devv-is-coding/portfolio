// Create project Start -------->
const createProjectForm = document.querySelector('#createProjectForm').addEventListener('submit', (event) => {
    event.preventDefault();

    const createProjectName = document.getElementById('createProjectName').value;
    const createProjectFilePath = document.getElementById('createProjectFilePath').files[0];

    // Log to check form data
    console.log('Project Name:', createProjectName);
    console.log('Selected File:', createProjectFilePath);

    // Create FormData object to handle file and text data
    const formData = new FormData();
    formData.append('projectName', createProjectName);  
    formData.append('projectFilePath', createProjectFilePath);

    // Send POST request to the server
    fetch('http://localhost:3000/create-project', {
        method: 'POST',
        body: formData 
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);  // Show server response message
        new bootstrap.Modal(document.querySelector('#CreateProjectModal')).hide();  // Close modal after submission
    })
    .catch(error => console.error('Error:', error));
});

// Update project Start -------->
const updateProjectForm = document.querySelector('#updateProjectForm').addEventListener('submit', (event) => { 
    event.preventDefault();

    const projectID = document.querySelector('#updateProjectID').value;
    const updateProjectName = document.querySelector('#updateProjectName').value;
    const updateProjectFilePath = document.querySelector('#updateProjectFilePath').files[0];

    // Log to check form data
    console.log('Project ID:', projectID);
    console.log('Updated Project Name:', updateProjectName);
    console.log('Updated Project File:', updateProjectFilePath);

    // Create FormData object to handle file and text data
    const updateFormData = new FormData();
    updateFormData.append('projectName', updateProjectName);  
    updateFormData.append('projectFilePath', updateProjectFilePath);

    // Send PUT request to the server
    fetch(`http://localhost:3000/update-project/${projectID}`, {
        method: 'PUT',
        body: updateFormData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);  // Show server response message
        new bootstrap.Modal(document.querySelector('#UpdateProjectModal')).hide();  // Close modal after submission
    })
    .catch(error => console.error('Error:', error));
});

// Delete project Start -------->
const deleteProject = (event) => {
    event.preventDefault();
    const projectID = document.querySelector('#deleteProjectID').value;
    if (!projectID) {
        alert("Please enter a Project ID.");
        return;
    } 
    fetch(`http://localhost:3000/delete-project/${projectID}`, { method: 'DELETE'})
   .then(response => response.json())
   .then(data => {
    alert(data.message);
    const hideDeleteModal = bootstrap.Modal.getInstance(document.getElementById('DeleteProjectModal')) || new bootstrap.Modal(document.getElementById('DeleteProjectModal'));
    hideDeleteModal.hide();
    const backDrop = document.querySelectorAll('.modal-backdrop');
    backDrop.forEach(el => el.remove());
   })
   .catch(error => console.error("Error: ", error));
};

const ViewBTN = document.querySelector('#ViewBTN').addEventListener('click', (event) =>{
    event.preventDefault();
    const projectID = document.querySelector('#viewProjectID').value;

    fetch(`http://localhost:3000/view-project/${projectID}`, { method: 'GET' })
        .then(response => {
            if (!response.ok) throw new Error('Project not found');
            return response.json();
        })
        .then(data => {
            // Populate modal with data
            const projectCreated = new Date(data.projectCreated);
            const formattedDate = projectCreated.toISOString().slice(0, 10); // Get "YYYY-MM-DD"
            const formattedTime = projectCreated.toTimeString().slice(0, 5); // Get "HH:MM"
            const projectID = document.querySelector('#viewProjectNameResultID');
            const projectName = document.querySelector('#viewProjectDescriptionResultID');
            const projectDateCreated = document.querySelector('#viewProjectDateResultID');
            projectID.textContent = `Project ID: ${data.projectID}`;
            projectName.textContent = `Project Name: ${data.projectName}`;
            projectDateCreated.textContent = `Date Created: ${formattedDate} ${formattedTime}`;

            
            const imgElement = document.querySelector('#viewProjectFilePathResult img');
            imgElement.src = `/images/${data.projectFilePath}`;
            imgElement.alt = data.projectName || 'Project Image';

            // Hide initial modal and show result modal
            const viewModal = new bootstrap.Modal(document.querySelector('#ViewProjectModal'));
            viewModal.hide();
            const resultModal = new bootstrap.Modal(document.querySelector('#ViewProjectModalResult'));
            resultModal.show();          
            console.log('test2');
            
            console.log(resultModal);
        })
        .catch(error => alert(error.message || "Error fetching project data"));
})

// View project Start -------->
// const viewProject = (VPID) => {
//     fetch(`http://localhost:3000/view-project/${VPID}`, { method: 'GET' })
//         .then(response => {
//             if (!response.ok) throw new Error('Project not found');
//             return response.json();
//         })
//         .then(data => {
//             // Populate modal with data
//             const projectCreated = new Date(data.projectCreated);
//             const formattedDate = projectCreated.toISOString().slice(0, 10); // Get "YYYY-MM-DD"
//             const formattedTime = projectCreated.toTimeString().slice(0, 5); // Get "HH:MM"
//             const projectID = document.querySelector('#viewProjectNameResultID');
//             const projectName = document.querySelector('#viewProjectDescriptionResultID');
//             const projectDateCreated = document.querySelector('#viewProjectDateResultID');
//             projectID.textContent = `Project ID: ${data.projectID}`;
//             projectName.textContent = `Project Name: ${data.projectName}`;
//             projectDateCreated.textContent = `Date Created: ${formattedDate} ${formattedTime}`;

            
//             const imgElement = document.querySelector('#viewProjectFilePathResult img');
//             imgElement.src = `/images/${data.projectFilePath}`;
//             imgElement.alt = data.projectName || 'Project Image';

//             // Hide initial modal and show result modal
//             const viewModal = bootstrap.Modal.getInstance(document.querySelector('#ViewProjectModal'));
//             if (viewModal) {
//             viewModal.hide();
//             console.log('test');
//             }
//             const resultModal = new bootstrap.Modal(document.querySelector('#ViewProjectModalResult'));
//             resultModal.show();            
//                 console.log('test2');
            
//             console.log(resultModal);
//         })
//         .catch(error => alert(error.message || "Error fetching project data"));
// };

// View all projects start -------->
const viewAllProjects = () => {
    fetch('http://localhost:3000/view-all-projects', 
        { method: 'GET' }
    ) 
        .then(response => response.json())
        .then(data => {
            const projectsContainer = document.querySelector('#projectsContainer');

            projectsContainer.innerHTML = '';

            data.forEach(project => {
                const projectCreated = new Date(project.projectCreated);
                const formattedDate = projectCreated.toDateString();
                let formattedTimeHours = projectCreated.getHours();
                let formattedTimeMinutes = projectCreated.getMinutes();
                let amOrPm = formattedTimeHours >= 12 ? 'PM' : 'AM';

                formattedTimeHours = formattedTimeHours % 12 || 12;
                formattedTimeMinutes = formattedTimeMinutes < 10 ? '0' + formattedTimeMinutes : formattedTimeMinutes;
                
                let time = formattedTimeHours + ':' + formattedTimeMinutes + amOrPm;
                

                const projectElement = document.createElement('div');
                projectElement.className = 'card mb-3';
                projectElement.innerHTML = `
                    <div class="row g-0">
                        <div class="col-md-4">
                            <img src="/images/${project.projectFilePath}" alt="${project.projectName || 'Project Image'}" class="img-fluid rounded-start">
                        </div>
                        <div class="col-md-8">
                            <div class="card-body">
                                <h5 class="card-title">Project ID: ${project.projectID}</h5>
                                <p class="card-text">Project Name: ${project.projectName || 'No description available.'}</p>
                                <p class="card-text2">Project Created: Date: ${formattedDate || 'No information available.'} Time: ${time} </p>
                            </div>
                        </div>
                    </div>
                `;
                projectsContainer.appendChild(projectElement);
            });
        })
        .catch(error => console.error('Error:', error));
};

document.addEventListener('DOMContentLoaded', viewAllProjects);








